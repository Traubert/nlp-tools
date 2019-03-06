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
%template(ScoredWord) std::pair<std::string, float>;
%template(ScoredWords) std::vector<ScoredWord>;
%template(WVector) std::vector<WordVecFloat>;
%template(WordWithVector) std::pair<std::string, WVector>;

struct WordEmbeddings {
    void load_from_file(std::string filename);
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
    WordVecFloat get_distance(const std::string& word1, const std::string& word2) const;
    WordWithVector get_embedding(const std::string & word) const;
};
