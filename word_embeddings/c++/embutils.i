%module embutils
%{
#include "embutils.h"
%}

typedef float WordVecFloat;
typedef std::pair<std::string, WordVecFloat> ScoredWord;
typedef std::vector<ScoredWord> ScoredWords;
typedef std::vector<WordVecFloat> WVector;
typedef std::pair<std::string, WVector> WordWithVector;

%include <std_string.i>
%include <std_vector.i>
%include <std_pair.i>
%include <exception.i>
%template(ScoredWord) std::pair<std::string, float>;
%template(ScoredWords) std::vector<ScoredWord>;
%template(WVector) std::vector<WordVecFloat>;
%template(WordWithVector) std::pair<std::string, WVector>;

%exception {
    try { $action } catch (std::runtime_error & e) {
        std::string s(e.what());
        SWIG_exception(SWIG_RuntimeError, s.c_str());
    }
 }

struct WordEmbeddings {
    void load_from_file(std::string filename,
                        unsigned int limit = 0);
    void load_from_file(std::string filename,
                        float fraction);
    ScoredWords like(const std::string & word,
                     unsigned int nwords = 10) const;
    
    ScoredWords like(const std::string & word1, const std::string & word2,
                     unsigned int nwords = 10,
                     WordVecFloat vector_similarity_projection_factor = 1.0)
        const;
    
    ScoredWords unlike(const std::string & word1, const std::string & word2,
                       unsigned int nwords = 10,
                       WordVecFloat vector_similarity_projection_factor = 1.0)
        const;

    ScoredWords get_words_at_distance_under(
        const std::string & comparison_word,
        WordVecFloat distance) const;
    
    WordVecFloat get_distance(const std::string& word1, const std::string& word2) const;
    
    WordWithVector get_embedding(const std::string & word) const;
};
