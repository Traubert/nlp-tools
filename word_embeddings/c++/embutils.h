#pragma once

#include <time.h>
#include <iomanip>
#include <cmath>
#include <string>
#include <exception>
#include <vector>
#include <iostream>
#include <fstream>
#include <sstream>
#include <functional>
#include <memory>

struct WordEmbedding;

typedef std::pair<std::string, std::string> StringPair;
typedef float WordVecFloat;
typedef std::vector<WordVecFloat> RawVector;
typedef std::vector<std::string> StringVector;
typedef std::vector<WordEmbedding> WordEmbeddingVector;
typedef std::pair<WordEmbedding, WordVecFloat> ScoredEmbedding;
typedef std::vector<ScoredEmbedding> ScoredEmbeddings;
typedef std::pair<std::string, WordVecFloat> ScoredWord;
typedef std::vector<ScoredWord> ScoredWordVector;

// For swig
typedef std::pair<std::string, RawVector> WordWithVector;

class Vector: public RawVector{
    WordVecFloat cached_norm;
public:
    Vector(void);
    Vector(RawVector v);
    void cache_norm(void);
    WordVecFloat get_norm(void) const { return cached_norm; }
    WordVecFloat cosine_distance(const Vector & other) const;
};

struct WordEmbedding {
    std::string word;
    Vector vector;

    WordEmbedding(void): word("") {}
    WordEmbedding(const std::string & s): word(s) {}
    WordVecFloat cosine_distance(const WordEmbedding & other) const;
    WordVecFloat cosine_distance(const Vector & other) const;
};

class ScoredWords: public ScoredWordVector
{
public:
    using ScoredWordVector::ScoredWordVector;
    ScoredWords(const ScoredEmbeddings & embs)
        {
            reserve(embs.size());
            for (const auto & it : embs) {
                push_back(ScoredWord((it.first).word, it.second));
            }
        }
};

class LikeUnlikeTransformer {
    RawVector comparison_point_cache;
    RawVector plane_vec;
    bool negative;
    WordVecFloat plane_vec_square_sum;
    WordVecFloat comparison_point_norm;
    WordVecFloat translation_term;
    WordVecFloat projection_factor;
    
public:
    LikeUnlikeTransformer(
        const RawVector & first_point,
        const RawVector & second_point,
        bool is_negative,
        WordVecFloat vector_similarity_projection_factor = 1.0);

    Vector operator() (const Vector & original);

    const RawVector & get_comparison_point(void) { return comparison_point_cache; }
};

class LikeUnlikeTransformerChain: public std::vector<LikeUnlikeTransformer> {

public:
    Vector operator() (const Vector & original)
        {
            Vector transformed(original);
            for (auto it : *this) {
                transformed = it(transformed);
            }
            return transformed;
        }

    Vector get_final_comparison_point(void)
        {
            if (size() == 0) {
                return Vector();
            }
            Vector retval = begin()->get_comparison_point();
            if (size() == 1) {
                return retval;
            }
            for (auto it = begin() + 1; it != end(); ++it) {
                retval = (*it)(retval);
            }
            return retval;
        }
};

class LikeArgs;

class WordEmbeddings: public WordEmbeddingVector {
    size_t dimension;
    
   
    ScoredEmbeddings get_top_n(
        const Vector & _comparison_point,
        size_t n = 10) const;

    ScoredEmbeddings get_top_n(
        const WordEmbedding & _comparison_point,
        size_t n = 10) const;

    ScoredEmbeddings get_top_n_in_transformed_space(
        size_t n,
        const RawVector & comparison_point,
        const RawVector & plane_vec,
        WordVecFloat translation_term,
        bool negative,
        WordVecFloat vector_similarity_projection_factor = 1.0) const;

    ScoredWords get_top_n_words_in_transformed_space(
        size_t n,
        const RawVector & comparison_point,
        const RawVector & plane_vec,
        WordVecFloat translation_term,
        bool negative,
        WordVecFloat vector_similarity_projection_factor = 1.0) const;

    ScoredWords get_top_n_words_in_transformed_space(
        size_t n,
        LikeUnlikeTransformerChain transformer) const;
    ScoredEmbeddings get_top_n_in_transformed_space(
        size_t n,
        LikeUnlikeTransformerChain transformer) const;
    
    ScoredWords get_top_n_words(
        const Vector & comparison_point,
        size_t n = 10) const;

    ScoredWords get_top_n_words(
        const WordEmbedding & comparison_point,
        size_t n = 10) const;

public:
    
    void load_from_file(const std::string & filename,
                        float fraction);
    void load_from_file(const std::string & filename,
                        unsigned int limit = 0);
    void load_from_file(
        const std::string & filename,
        std::function<unsigned int (size_t lexicon_size)> limiter);

    WordEmbedding get(const std::string & word) const;
    WordEmbedding get_exact(const std::string & word) const;

    WordWithVector get_embedding(const std::string & word) const;
    
    WordVecFloat get_distance(const std::string& word1, const std::string& word2) const;

    ScoredWords get_words_at_distance_under(
        const std::string & comparison_word,
        WordVecFloat distance) const;

    ScoredWords like(const std::string & word,
                     unsigned int nwords = 10) const;
    
    ScoredWords like(const std::string & word1, const std::string & word2,
                     unsigned int nwords, bool negative,
                     WordVecFloat vector_similarity_projection_factor = 1.0) const;

    ScoredWords like(LikeArgs args, unsigned int nwords = 10) const;

    ScoredWords like(const std::string & word1, const std::string & word2,
                     unsigned int nwords = 10, WordVecFloat vector_similarity_projection_factor = 1.0) const;

    ScoredWords unlike(const std::string & word1, const std::string & word2,
                       unsigned int nwords = 10, WordVecFloat vector_similarity_projection_factor = 1.0) const;

};

struct LikeArgs {
    bool negative;
    WordVecFloat projection_factor;
    std::shared_ptr<LikeArgs> left;
    std::shared_ptr<LikeArgs> right;
    WordEmbedding embedding;
public:
    LikeArgs(void): negative(false), projection_factor(1.0),
                    left(std::shared_ptr<LikeArgs>(nullptr)), right(std::shared_ptr<LikeArgs>(nullptr)) {}
    LikeArgs(std::string l,
             std::string r,
             bool _negative,
             WordVecFloat _projection_factor = 1.0):
        negative(_negative), projection_factor(_projection_factor) {
        left = std::make_shared<LikeArgs>(l);
        right = std::make_shared<LikeArgs>(r);
    };
    LikeArgs(std::string word): embedding(word), left(nullptr), right(nullptr) {}

    LikeArgs(std::shared_ptr<LikeArgs> l,
             std::shared_ptr<LikeArgs> r,
             bool _negative,
             WordVecFloat _projection_factor = 1.0):
        left(l), right(r), negative(_negative), projection_factor(_projection_factor) {};
    LikeArgs(std::shared_ptr<LikeArgs> emb,
             bool _negative,
             WordVecFloat _projection_factor = 1.0):
        embedding(emb->embedding), left(nullptr), right(nullptr), negative(_negative), projection_factor(_projection_factor) {};

    LikeArgs(LikeArgs l,
             LikeArgs r,
             bool _negative,
             WordVecFloat _projection_factor = 1.0):
        left(std::make_shared<LikeArgs>(l)), right(std::make_shared<LikeArgs>(r)), negative(_negative), projection_factor(_projection_factor) {};
    LikeArgs(LikeArgs emb,
             bool _negative,
             WordVecFloat _projection_factor = 1.0):
        embedding(emb.embedding), left(nullptr), right(nullptr), negative(_negative), projection_factor(_projection_factor) {};
    
    LikeUnlikeTransformerChain get_transformer_chain(void);
    virtual void embed(const WordEmbeddings & embs);
    bool is_leaf(void)
        { return left.get() == nullptr && right.get() == nullptr; }
};

RawVector operator-(RawVector l, const RawVector & r);
RawVector operator+(RawVector l, const RawVector & r);
RawVector pointwise_multiplication(RawVector l, const RawVector & r);
RawVector scalar_multiplication(WordVecFloat l, RawVector r);
WordVecFloat dot_product(const RawVector & l, const RawVector & r);
template <typename T> WordVecFloat square_sum(const std::vector<T> & v);
WordVecFloat norm(const RawVector & v);

