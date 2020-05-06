#include "embutils.h"

Vector::Vector(void) {
    cached_norm = 0.0;
}

Vector::Vector(RawVector v): RawVector(v) {
    cache_norm();
}
    
void Vector::cache_norm(void) {
    cached_norm = norm(*this);
}

WordVecFloat Vector::cosine_distance(const Vector & other) const
{
    // Sometimes very nearby vectors combined with rounding error will produce
    // a slightly negative distance, so make sure to return at least 0.0
    WordVecFloat retval = 1.0 - dot_product(*this, other) /
        (cached_norm * other.cached_norm);
    return std::max(static_cast<WordVecFloat>(0.0), retval);
}

WordVecFloat WordEmbedding::cosine_distance(const WordEmbedding & other) const
{
    return vector.cosine_distance(other.vector);
}

WordVecFloat WordEmbedding::cosine_distance(const Vector & other) const
{
    return vector.cosine_distance(other);
}

void WordEmbeddings::load_from_file(const std::string & filename,
                                    float fraction)
{
    load_from_file(filename,
                   [=] (size_t lexicon_size) {
                       return static_cast<unsigned int>(fraction * lexicon_size);
                   });
}

void WordEmbeddings::load_from_file(const std::string & filename,
                                    unsigned int limit)
{
    load_from_file(filename,
                   [=] (size_t lexicon_size) {
                       return limit;
                   });
}

void WordEmbeddings::load_from_file(
    const std::string & filename,
    std::function<unsigned int (size_t lexicon_size)> limiter)
{
    clear();
    dimension = 0;
    bool binary_format = false;
    if (filename.rfind(".bin") == filename.size() - 4) {
        binary_format = true;
    }
    char separator = ' ';
    std::ifstream infile;
    std::string line;
    unsigned int lexicon_size;
    infile.open(filename.c_str());
    if(!infile.good()) {
        std::cerr << "could not open vector file " << filename <<
            " for reading\n";
        return;
    }
    std::getline(infile, line);
    std::stringstream ss(line);
    ss >> lexicon_size;
    ss.ignore(1);
    ss >> dimension;
    unsigned int limit = limiter(lexicon_size);
    if (limit > 0 && limit < lexicon_size) {
        lexicon_size = limit;
    }
    reserve(lexicon_size);
    size_t words_read = 0;
    if (binary_format) {
        while (infile.good() && words_read < lexicon_size) {
            std::getline(infile, line, separator);
            if (words_read == 0 && line == "</s>") {
                infile.ignore(sizeof(WordVecFloat) * dimension + 1);
                ++words_read;
                continue;
            }
            WordEmbedding we;
            we.vector.resize(dimension);
            infile.read((char*)&(we.vector[0]), sizeof(WordVecFloat) * dimension);
            infile.ignore(1);
            we.vector.cache_norm();
            we.word = line;
            push_back(we);
            ++words_read;
        }
    } else {
        while(infile.good() && words_read < lexicon_size) {
            std::getline(infile, line);
            if (line.empty()) { continue; }
            ++words_read;
            size_t pos = line.find(separator);
            if (pos == std::string::npos) {
                std::cerr << "warning: text vector file " << filename <<
                    " doesn't appear to be space-separated\n  (reading line " << words_read + 1 << ")\n";
                break;
            }
            std::string word = line.substr(0, pos);
            RawVector components;
            components.reserve(dimension);
            size_t nextpos;
            while (std::string::npos != (nextpos = line.find(separator, pos + 1))) {
                components.push_back(strtod(line.substr(pos + 1, nextpos - pos).c_str(), NULL));
                pos = nextpos;
            }
            // there can be one more from pos to the newline if there isn't a
            // separator at the end
            if (line.back() != separator) {
                components.push_back(strtof(line.substr(pos + 1).c_str(), NULL));
            }
            if (size() != 0 && begin()->vector.size() != components.size()) {
                std::cerr << "warning: vector file " << filename <<
                    " appears malformed\n  (reading line " << words_read + 1 << ")\n";
                continue;
            }
            WordEmbedding we;
            we.word = word;
            we.vector = Vector(components);
            push_back(we);
        }
    }
    infile.close();
    if (size() == 0) {
        std::cerr << "Tried to read word vector file, empty result\n";
    }
    if (false) {
        std::cerr << "Read " << size() << " vectors of dimensionality " << begin()->vector.size() << std::endl;
    }
}

WordEmbedding WordEmbeddings::get(const std::string & word) const
{
    size_t best_prefix = 0;
    size_t best_suffix = 0;
    WordEmbeddings::const_iterator best_by_prefix;
    WordEmbeddings::const_iterator best_by_suffix;
    for (auto it = begin(); it != end(); ++it) {
        std::string::const_iterator w_it = word.begin();
        std::string::const_iterator t_it = it->word.begin();
        while(true) {
            if (w_it == word.end() && t_it == it->word.end()) {
                // matched
                return *it;
            }
            else if (w_it == word.end() || t_it == it->word.end() || *w_it != *t_it) {
                break;
            }
            else {
                ++w_it; ++t_it;
            }
        }
        if (w_it == word.end()) {
            // word ended first, can't get a better suffix than this
            if (word.size() > best_prefix) {
                best_prefix = word.size();
                best_by_prefix = it;
            }
            continue;
        } else if (t_it == it->word.end()) {
                // iterator ended before word, iterator is full prefix
            if (it->word.size() > best_prefix) {
                best_prefix = it->word.size();
                best_by_prefix = it;
            }
            continue;
        } else {
            // They differed here
            if (w_it - word.begin() > best_prefix) {
                best_prefix = (w_it - word.begin());
                best_by_prefix = it;
            }
            // Then we see about the suffix
            std::string::const_reverse_iterator w_it = word.rbegin();
            std::string::const_reverse_iterator t_it = it->word.rbegin();

            while (true) {
                if (w_it == word.rend() || t_it == it->word.rend() || *w_it != *t_it) {
                    break;
                } else {
                    ++w_it; ++t_it;
                }
            }
            if (w_it == word.rend()) {
                // word reverse ended first
                if (word.size() > best_suffix) {
                    best_suffix = word.size();
                    best_by_suffix = it;
                }
                continue;
            } else if (t_it == it->word.rend()) {
                if (it->word.size() > best_suffix) {
                    best_suffix = it->word.size();
                    best_by_suffix = it;
                }
                continue;
            } else {
                if (w_it - word.rbegin() > best_suffix) {
                    best_suffix = (w_it - word.rbegin());
                    best_by_suffix = it;
                }
            }
        }
    }

    if (best_suffix > best_prefix) {
        return *best_by_suffix;
    } else if (best_prefix > 0) {
        return *best_by_prefix;
    } else {
        throw std::runtime_error("requested word " + word + " not present");
    }
}

WordEmbedding WordEmbeddings::get_exact(const std::string & word) const
{
    for (auto it = begin(); it != end(); ++it) {
        if (word == it->word) {
            return *it;
        }
    }
    throw std::runtime_error("requested word " + word + " not present");
}

WordWithVector WordEmbeddings::get_embedding(const std::string & word) const
{
    try {
        WordEmbedding emb = get(word);
        return WordWithVector(emb.word, emb.vector);
    } catch (std::runtime_error & e) {
        return WordWithVector("", RawVector(dimension, 0.0));
    }
}

WordVecFloat WordEmbeddings::get_distance(const std::string& word1, const std::string& word2) const
{
    WordEmbedding emb1 = get(word1);
    WordEmbedding emb2 = get(word2);
    return emb1.cosine_distance(emb2);
}

// Get the n best candidates in the original space using an insertion sort
ScoredEmbeddings WordEmbeddings::get_top_n(const Vector & comparison_point,
                                           size_t n) const
{
    ScoredEmbeddings retval;
    retval.reserve(n + 1);
    for (auto it = begin(); it != end(); ++it) {
        WordVecFloat cosdist = it->cosine_distance(comparison_point);
        for (size_t i = retval.size();; --i) {
            if (i == 0) {
                // We got to the top
                ScoredEmbedding new_val = std::pair<WordEmbedding, WordVecFloat>(
                    WordEmbedding(*it), cosdist);
                retval.insert(retval.begin(), new_val);
                break;
            } else if (cosdist >= retval[i - 1].second) {
                // This value is worse than the one ahead of us
                if (i == n) {
                    // We didn't make the list
                } else {
                    // We make this a new list member
                    ScoredEmbedding new_val = std::pair<WordEmbedding, WordVecFloat>(
                        WordEmbedding(*it), cosdist);
                    retval.insert(retval.begin() + i, new_val);
                }
                break;
            } else {
                // We move up the list
                continue;
            }
        }
        if (retval.size() > n) {
            retval.pop_back();
        }
    }
    return retval;
}

ScoredEmbeddings WordEmbeddings::get_top_n(const WordEmbedding & comparison_point,
                                           size_t n) const
{
    return get_top_n(comparison_point.vector, n);
}

ScoredWords WordEmbeddings::get_words_at_distance_under(
    const std::string & comparison_word,
    WordVecFloat distance) const
{
    WordEmbedding comparison_point = get(comparison_word);
    ScoredWords retval;
    for (auto it = begin(); it != end(); ++it) {
        if (comparison_word == it->word) {
            continue;
        }
        WordVecFloat cosdist = it->cosine_distance(comparison_point);
        if (cosdist <= distance) {
            ScoredWord new_val(it->word, cosdist);
            for (size_t i = 0;; ++i) {
                if (i == retval.size()) {
                    retval.push_back(new_val);
                    break;
                } else if (retval[i].second <= cosdist) {
                    continue;
                } else {
                    retval.insert(retval.begin() + i, new_val);
                    break;
                }
            }
        }
    }
    return retval;
}

LikeUnlikeTransformer::LikeUnlikeTransformer(
    const RawVector & first_point,
    const RawVector & second_point,
    bool is_negative,
    WordVecFloat vector_similarity_projection_factor):
    negative(is_negative),
    projection_factor(vector_similarity_projection_factor)
{

    /*
     * When there are two vectors A and B, we compute the vector A - B that
     * goes from one to the other, and define a hyperplane orthogonal to that
     * vector that intersects the vector at the midpoint between the
     * two. We then add to all vectors a multiple of A - B to move them closer
     * to the plane, reducing the distance that is due to the difference
     * between A and B. (This is like projecting the space to the hyperplane
     * if we go all the way to the plane)
     *
     * The hyperplane is defined by the equation |B - A| = d, where d is a
     * translation term. |B - A| = 0 would be the set of vectors orthogonal to
     * |B - A|. We set d so that the distance from the hyperplane to A is
     * half of the norm of |B - A|.
     *
     */

    plane_vec = first_point - second_point;
    plane_vec_square_sum = square_sum(plane_vec);
    translation_term = dot_product(plane_vec, first_point)
        - plane_vec_square_sum * 0.5;

    if (is_negative == true) {
        WordVecFloat comparison_scaler =
            (translation_term - dot_product(first_point, plane_vec)) / plane_vec_square_sum;
        comparison_scaler *= vector_similarity_projection_factor;
        comparison_point_cache = first_point - scalar_multiplication(comparison_scaler, plane_vec);
    } else {
        comparison_point_cache = second_point + scalar_multiplication(static_cast<WordVecFloat>(0.5), plane_vec);
    }
    plane_vec_square_sum = square_sum(plane_vec);
    comparison_point_norm = norm(comparison_point_cache);

}

Vector LikeUnlikeTransformer::operator() (const Vector & original)
{
    Vector transformed(original);
    /*
     * Given a plane "plane_vec = translation term" and a point,
     * find the multiple of plane_vec which produces a vector going
     * from point to the nearest point in the plane.
     */
    
    WordVecFloat transformed_vec_scaler =
        (translation_term - dot_product(transformed, plane_vec))
        / plane_vec_square_sum;
    transformed_vec_scaler *= projection_factor;
    if(negative) {
        transformed =
            Vector(transformed - scalar_multiplication(transformed_vec_scaler, plane_vec));
    } else {
        transformed =
            Vector(transformed + scalar_multiplication(transformed_vec_scaler, plane_vec));
    }
    return transformed;
}

// Get the n best candidates in the transformed space using an insertion sort
ScoredEmbeddings WordEmbeddings::get_top_n_in_transformed_space(
    size_t n,
    const RawVector & _comparison_point,
    const RawVector & plane_vec,
    WordVecFloat translation_term,
    bool negative,
    WordVecFloat vector_similarity_projection_factor) const
{
    ScoredEmbeddings retval;
    Vector comparison_point(_comparison_point);
    WordVecFloat plane_vec_square_sum = square_sum(plane_vec);
    for (WordEmbeddings::const_iterator it = this->begin();
         it != this->end(); ++it) {
        Vector transformed_vec(it->vector);

        /*
         * First, given a plane "plane_vec = translation term" and a point,
         * find the multiple of plane_vec which produces a vector going
         * from point to the nearest point in the plane.
         */

        WordVecFloat transformed_vec_scaler =
            (translation_term - dot_product(transformed_vec, plane_vec))
            / plane_vec_square_sum;
        transformed_vec_scaler *= vector_similarity_projection_factor;
        if(negative) {
            transformed_vec =
                Vector(transformed_vec - scalar_multiplication(transformed_vec_scaler, plane_vec));
        } else {
            transformed_vec =
                Vector(transformed_vec + scalar_multiplication(transformed_vec_scaler, plane_vec));
        }
        WordVecFloat cosdist = comparison_point.cosine_distance(transformed_vec);
        retval.reserve(n + 1);
        for (size_t i = retval.size();; --i) {
            if (i == 0) {
                // We got to the top
                ScoredEmbedding new_val = std::pair<WordEmbedding, WordVecFloat>(
                    WordEmbedding(*it), cosdist);
                retval.insert(retval.begin(), new_val);
                break;
            } else if (cosdist >= retval[i - 1].second) {
                // This value is worse than the one ahead of us
                if (i == n) {
                    // We didn't make the list
                } else {
                    // We make this a new list member
                    ScoredEmbedding new_val = std::pair<WordEmbedding, WordVecFloat>(
                        WordEmbedding(*it), cosdist);
                    retval.insert(retval.begin() + i, new_val);
                }
                break;
            } else {
                // We move up the list
                continue;
            }
        }
        if (retval.size() > n) {
            retval.pop_back();
        }
    }
    return retval;
}

ScoredWords WordEmbeddings::get_top_n_words_in_transformed_space(
    size_t n,
    const RawVector & _comparison_point,
    const RawVector & plane_vec,
    WordVecFloat translation_term,
    bool negative,
    WordVecFloat vector_similarity_projection_factor) const
{
    return get_top_n_in_transformed_space(
        n, _comparison_point, plane_vec, translation_term, negative,
        vector_similarity_projection_factor);
}

ScoredEmbeddings WordEmbeddings::get_top_n_in_transformed_space(
    size_t n,
    LikeUnlikeTransformerChain transformer) const
{
    ScoredEmbeddings retval;
    Vector comparison_point(transformer.get_final_comparison_point());
    for (WordEmbeddings::const_iterator it = this->begin();
         it != this->end(); ++it) {
        Vector transformed_vec = transformer(it->vector);
        WordVecFloat cosdist = comparison_point.cosine_distance(transformed_vec);
        retval.reserve(n + 1);
        for (size_t i = retval.size();; --i) {
            if (i == 0) {
                // We got to the top
                ScoredEmbedding new_val = std::pair<WordEmbedding, WordVecFloat>(
                    WordEmbedding(*it), cosdist);
                retval.insert(retval.begin(), new_val);
                break;
            } else if (cosdist >= retval[i - 1].second) {
                // This value is worse than the one ahead of us
                if (i == n) {
                    // We didn't make the list
                } else {
                    // We make this a new list member
                    ScoredEmbedding new_val = std::pair<WordEmbedding, WordVecFloat>(
                        WordEmbedding(*it), cosdist);
                    retval.insert(retval.begin() + i, new_val);
                }
                break;
            } else {
                // We move up the list
                continue;
            }
        }
        if (retval.size() > n) {
            retval.pop_back();
        }
    }
    return retval;
}

ScoredWords WordEmbeddings::get_top_n_words_in_transformed_space(
    size_t n,
    LikeUnlikeTransformerChain transformer) const
{
    return get_top_n_in_transformed_space(n, transformer);
}

ScoredWords WordEmbeddings::get_top_n_words(const Vector & comparison_point,
                                            size_t n) const
{
    ScoredWords retval;
    retval.reserve(n);
    ScoredEmbeddings embs = this->get_top_n(comparison_point, n);
    for (auto it = embs.begin(); it != embs.end(); ++it) {
        retval.push_back(ScoredWord((it->first).word, it->second));
    }
    return retval;
}

ScoredWords WordEmbeddings::get_top_n_words(const WordEmbedding & comparison_point,
                                            size_t n) const
{
    return get_top_n_words(comparison_point.vector, n);
}

ScoredWords WordEmbeddings::like(const std::string & word, unsigned int nwords) const

{
    return get_top_n_words(get(word), nwords);
}

ScoredWords WordEmbeddings::like(const std::string & word1, const std::string & word2,
                                 unsigned int nwords, bool is_negative,
                                 WordVecFloat vector_similarity_projection_factor) const
{
    WordEmbedding this_word1 = get(word1);
    WordEmbedding this_word2 = get(word2);
    LikeUnlikeTransformerChain chain;
    LikeUnlikeTransformer transformer(this_word1.vector, this_word2.vector, is_negative, vector_similarity_projection_factor);
    chain.push_back(transformer);
    return get_top_n_words_in_transformed_space(nwords,
                                                chain);
}

void LikeArgs::embed(const WordEmbeddings & embs)
{
    if (left) { left->embed(embs); }
    if (right) { right->embed(embs); }
    if (embedding.word.size() > 0) {
        embedding = embs.get(embedding.word);
    }
}

LikeUnlikeTransformerChain LikeArgs::get_transformer_chain(void)
{
    LikeUnlikeTransformerChain retval;
    if (left->is_leaf() && right->is_leaf()) {
        retval.push_back(LikeUnlikeTransformer(left->embedding.vector,
                                               right->embedding.vector,
                                               negative,
                                               projection_factor));
        return retval;
    } else if (right->is_leaf()) {
        LikeUnlikeTransformerChain l = left->get_transformer_chain();
        retval.insert(retval.end(), l.begin(), l.end());
        LikeUnlikeTransformer root(retval.get_final_comparison_point(),
                                   right->embedding.vector,
                                   negative,
                                   projection_factor);
        retval.push_back(root);
        return retval;
    }
    LikeUnlikeTransformerChain l = left->get_transformer_chain();
    retval.insert(retval.end(), l.begin(), l.end());
    LikeUnlikeTransformerChain r = right->get_transformer_chain();
    retval.insert(retval.end(), r.begin(), r.end());
    return retval;
}

ScoredWords WordEmbeddings::like(LikeArgs args,
                                 unsigned int nwords) const
{
//    auto embedder = std::bind(&WordEmbeddings::get, *this);
//    std::function<WordEmbedding (const std::string & word)> embedder_fobj(embedder);
    args.embed(*this);
    // turn strings into Vectors
    LikeUnlikeTransformerChain transformer = args.get_transformer_chain();
    // needs to able to chain computations
    return get_top_n_words_in_transformed_space(nwords, transformer);
    // WordEmbedding this_word1 = get(word1);
    // WordEmbedding this_word2 = get(word2);
    // WordEmbedding this_word3 = get(word3);
    // LikeUnlikeTransformer transformer(this_word1.vector, this_word2.vector, is_negative, vector_similarity_projection_factor);
    // RawVector comparison = transformer.get_comparison_point();
    // LikeUnlikeTransformer transformer2(comparison, transformer(this_word3.vector), is_negative, vector_similarity_projection_factor);
    // return get_top_n_words_in_transformed_space(nwords,
    //                                             transformer2);
}

ScoredWords WordEmbeddings::like(const std::string & word1, const std::string & word2,
                                 unsigned int nwords,
                                 WordVecFloat vector_similarity_projection_factor) const
{
    return like(word1, word2, nwords, false, vector_similarity_projection_factor);
}

ScoredWords WordEmbeddings::unlike(const std::string & word1, const std::string & word2,
                                 unsigned int nwords,
                                 WordVecFloat vector_similarity_projection_factor) const
{
    return like(word1, word2, nwords, true, vector_similarity_projection_factor);
}

RawVector operator-(RawVector l,
                 const RawVector & r)
{
    for(size_t i = 0; i < l.size(); ++i) {
        l[i] -= r[i];
    }
    return l;
}

RawVector operator+(RawVector l,
                 const RawVector & r)
{
    for(size_t i = 0; i < l.size(); ++i) {
        l[i] += r[i];
    }
    return l;
}

RawVector pointwise_multiplication(RawVector l,
                                const RawVector & r)
{
    for(size_t i = 0; i < r.size(); ++i) {
        l[i] *= r[i];
    }
    return l;
}

RawVector scalar_multiplication(WordVecFloat l,
                                RawVector r)
{
    for(size_t i = 0; i < r.size(); ++i) {
        r[i] *= l;
    }
    return r;
}

WordVecFloat dot_product(const RawVector & l,
                         const RawVector & r)
{
    WordVecFloat ret = 0;
    for(size_t i = 0; i < l.size(); ++i) {
        ret += l[i] * r[i];
    }
    return ret;
}

template <typename T> WordVecFloat square_sum(const std::vector<T> & v)
{
    WordVecFloat ret = 0;
    for(size_t i = 0; i < v.size(); ++i) {
        ret += v[i] * v[i];
    }
    return ret;
}

WordVecFloat norm(const RawVector & v)
{
    return sqrt(square_sum(v));
}

int main(void)
{
    WordEmbeddings embs;
    embs.load_from_file("/srv/data/word2vec/GoogleNews-vectors-negative300.bin", 100000u);
//    auto like1 = std::make_shared<LikeArgs>("mouse", "keyboard", false);
//    auto like2 = std::make_shared<LikeArgs>("joystick", "cheese", true);
    LikeArgs like(LikeArgs("mouse", "keyboard", false), LikeArgs("screen"), true);
//    like.left = like1;
//    like.right = like2;
    for (auto it : embs.like(like)) {
        std::cerr << "('" << it.first << "', " << it.second << ")," << std::endl;
    }
}
