#include <liblekhika/lekhika_core.h>
#include <cstring>
#include <string>
#include <vector>
#include <iostream>

extern "C" {

typedef struct {
    Transliteration* tl;
    DictionaryManager* dict;
} LekhikaContext;

LekhikaContext* lekhika_create(const char* data_dir, const char* db_path) {
    try {
        LekhikaContext* ctx = new LekhikaContext();
        ctx->tl = new Transliteration(data_dir ? data_dir : "");
#ifdef HAVE_SQLITE3
        ctx->dict = new DictionaryManager(db_path ? db_path : "");
#else
        ctx->dict = nullptr;
#endif
        return ctx;
    } catch (const std::exception& e) {
        std::cerr << "Lekhika Error: " << e.what() << std::endl;
        return nullptr;
    }
}

void lekhika_destroy(LekhikaContext* ctx) {
    if (ctx) {
        delete ctx->tl;
        if (ctx->dict) delete ctx->dict;
        delete ctx;
    }
}

char* lekhika_transliterate(LekhikaContext* ctx, const char* input) {
    if (!ctx || !input) return nullptr;
    std::string result = ctx->tl->transliterate(input);
    char* c_res = (char*)malloc(result.length() + 1);
    strcpy(c_res, result.c_str());
    return c_res;
}

void lekhika_set_smart_correction(LekhikaContext* ctx, bool enable) {
    if (ctx) ctx->tl->setEnableSmartCorrection(enable);
}

void lekhika_set_auto_correct(LekhikaContext* ctx, bool enable) {
    if (ctx) ctx->tl->setEnableAutoCorrect(enable);
}

void lekhika_set_indic_numbers(LekhikaContext* ctx, bool enable) {
    if (ctx) ctx->tl->setEnableIndicNumbers(enable);
}

void lekhika_set_symbols_transliteration(LekhikaContext* ctx, bool enable) {
    if (ctx) ctx->tl->setEnableSymbolsTransliteration(enable);
}

// Dictionary management
int lekhika_find_words(LekhikaContext* ctx, const char* prefix, int limit, char*** results) {
#ifdef HAVE_SQLITE3
    if (!ctx || !ctx->dict || !prefix) return 0;
    std::vector<std::string> words = ctx->dict->findWords(prefix, limit);
    if (words.empty()) return 0;

    *results = (char**)malloc(sizeof(char*) * words.size());
    for (size_t i = 0; i < words.size(); ++i) {
        (*results)[i] = (char*)malloc(words[i].length() + 1);
        strcpy((*results)[i], words[i].c_str());
    }
    return (int)words.size();
#else
    return 0;
#endif
}

int lekhika_get_all_words_paginated(LekhikaContext* ctx, int limit, int offset, int sort_by, bool asc, char*** results) {
#ifdef HAVE_SQLITE3
    if (!ctx || !ctx->dict) return 0;
    
    DictionaryManager::SortColumn col = (sort_by == 0) ? DictionaryManager::ByWord : DictionaryManager::ByFrequency;
    auto words = ctx->dict->getAllWords(limit, offset, col, asc);
    if (words.empty()) return 0;

    *results = (char**)malloc(sizeof(char*) * words.size() * 2);
    for (size_t i = 0; i < words.size(); ++i) {
        (*results)[i*2] = (char*)malloc(words[i].first.length() + 1);
        strcpy((*results)[i*2], words[i].first.c_str());
        std::string freq = std::to_string(words[i].second);
        (*results)[i*2+1] = (char*)malloc(freq.length() + 1);
        strcpy((*results)[i*2+1], freq.c_str());
    }
    return (int)words.size();
#else
    return 0;
#endif
}

int lekhika_search_words(LekhikaContext* ctx, const char* query, char*** results) {
#ifdef HAVE_SQLITE3
    if (!ctx || !ctx->dict || !query) return 0;
    auto words = ctx->dict->searchWords(query);
    if (words.empty()) return 0;

    *results = (char**)malloc(sizeof(char*) * words.size() * 2);
    for (size_t i = 0; i < words.size(); ++i) {
        (*results)[i*2] = (char*)malloc(words[i].first.length() + 1);
        strcpy((*results)[i*2], words[i].first.c_str());
        std::string freq = std::to_string(words[i].second);
        (*results)[i*2+1] = (char*)malloc(freq.length() + 1);
        strcpy((*results)[i*2+1], freq.c_str());
    }
    return (int)words.size();
#else
    return 0;
#endif
}

void lekhika_remove_word(LekhikaContext* ctx, const char* word) {
#ifdef HAVE_SQLITE3
    if (ctx && ctx->dict && word) ctx->dict->removeWord(word);
#endif
}

void lekhika_free_words(char** words, int count) {
    if (words) {
        for (int i = 0; i < count; ++i) {
            if (words[i]) free(words[i]);
        }
        free(words);
    }
}

void lekhika_free_string(char* s) {
    if (s) free(s);
}

void lekhika_add_word(LekhikaContext* ctx, const char* word) {
#ifdef HAVE_SQLITE3
    if (ctx && ctx->dict && word) ctx->dict->addWord(word);
#endif
}

void lekhika_reset_dictionary(LekhikaContext* ctx) {
#ifdef HAVE_SQLITE3
    if (ctx && ctx->dict) ctx->dict->reset();
#endif
}

void lekhika_update_word_freq(LekhikaContext* ctx, const char* word, int freq) {
#ifdef HAVE_SQLITE3
    if (ctx && ctx->dict && word) ctx->dict->updateWordFrequency(word, freq);
#endif
}

}
