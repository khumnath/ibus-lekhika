import ctypes
import os

class LekhikaWrapper:
    def __init__(self, lib_path, data_dir, db_path):
        if not os.path.exists(lib_path):
            raise FileNotFoundError(f"Library not found: {lib_path}")
        
        self.lib = ctypes.CDLL(lib_path)
        
        # Define argtypes/restype for core functions
        self.lib.lekhika_create.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.lekhika_create.restype = ctypes.c_void_p
        
        self.lib.lekhika_destroy.argtypes = [ctypes.c_void_p]
        self.lib.lekhika_destroy.restype = None
        
        self.lib.lekhika_transliterate.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.lib.lekhika_transliterate.restype = ctypes.c_void_p
        
        self.lib.lekhika_set_smart_correction.argtypes = [ctypes.c_void_p, ctypes.c_bool]
        self.lib.lekhika_set_auto_correct.argtypes = [ctypes.c_void_p, ctypes.c_bool]
        self.lib.lekhika_set_indic_numbers.argtypes = [ctypes.c_void_p, ctypes.c_bool]
        self.lib.lekhika_set_symbols_transliteration.argtypes = [ctypes.c_void_p, ctypes.c_bool]
        
        # Use void_p for string arrays to prevent auto-conversion/pointer loss
        self.lib.lekhika_find_words.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))]
        self.lib.lekhika_find_words.restype = ctypes.c_int
        
        self.lib.lekhika_add_word.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.lib.lekhika_remove_word.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

        self.lib.lekhika_get_all_words_paginated.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_bool, 
            ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
        ]
        self.lib.lekhika_get_all_words_paginated.restype = ctypes.c_int

        self.lib.lekhika_search_words.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
        ]
        self.lib.lekhika_search_words.restype = ctypes.c_int
        
        self.lib.lekhika_reset_dictionary.argtypes = [ctypes.c_void_p]
        self.lib.lekhika_update_word_freq.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        
        self.lib.lekhika_free_words.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
        self.lib.lekhika_free_string.argtypes = [ctypes.c_void_p]
        
        # Create context
        self.ctx = self.lib.lekhika_create(data_dir.encode('utf-8'), db_path.encode('utf-8'))
        if not self.ctx:
            raise Exception("Failed to create Lekhika context")
            
    def __del__(self):
        if hasattr(self, 'ctx') and self.ctx:
            self.lib.lekhika_destroy(self.ctx)
            
    def transliterate(self, text):
        res_ptr = self.lib.lekhika_transliterate(self.ctx, text.encode('utf-8'))
        if res_ptr:
            res = ctypes.c_char_p(res_ptr).value.decode('utf-8')
            self.lib.lekhika_free_string(res_ptr)
            return res
        return text
        
    def set_options(self, smart=None, auto=None, numbers=None, symbols=None):
        if smart is not None: self.lib.lekhika_set_smart_correction(self.ctx, smart)
        if auto is not None: self.lib.lekhika_set_auto_correct(self.ctx, auto)
        if numbers is not None: self.lib.lekhika_set_indic_numbers(self.ctx, numbers)
        if symbols is not None: self.lib.lekhika_set_symbols_transliteration(self.ctx, symbols)
        
    def find_words(self, prefix, limit=10):
        words_ptr = ctypes.POINTER(ctypes.c_void_p)()
        count = self.lib.lekhika_find_words(self.ctx, prefix.encode('utf-8'), limit, ctypes.byref(words_ptr))
        results = []
        if count > 0:
            for i in range(count):
                # Convert void_p to string
                s_ptr = words_ptr[i]
                results.append(ctypes.c_char_p(s_ptr).value.decode('utf-8'))
            self.lib.lekhika_free_words(words_ptr, count)
        return results

    def add_word(self, word):
        self.lib.lekhika_add_word(self.ctx, word.encode('utf-8'))

    def remove_word(self, word):
        self.lib.lekhika_remove_word(self.ctx, word.encode('utf-8'))

    def reset_dictionary(self):
        self.lib.lekhika_reset_dictionary(self.ctx)

    def update_word_freq(self, word, freq):
        self.lib.lekhika_update_word_freq(self.ctx, word.encode('utf-8'), freq)

    def get_all_words(self, limit=50, offset=0, sort_by=0, ascending=True):
        words_ptr = ctypes.POINTER(ctypes.c_void_p)()
        count = self.lib.lekhika_get_all_words_paginated(
            self.ctx, limit, offset, sort_by, ascending, ctypes.byref(words_ptr)
        )
        results = []
        if count > 0:
            for i in range(count):
                word = ctypes.c_char_p(words_ptr[i*2]).value.decode('utf-8')
                freq = int(ctypes.c_char_p(words_ptr[i*2+1]).value.decode('utf-8'))
                results.append((word, freq))
            self.lib.lekhika_free_words(words_ptr, count * 2)
        return results

    def search_words(self, query):
        words_ptr = ctypes.POINTER(ctypes.c_void_p)()
        count = self.lib.lekhika_search_words(self.ctx, query.encode('utf-8'), ctypes.byref(words_ptr))
        results = []
        if count > 0:
            for i in range(count):
                word = ctypes.c_char_p(words_ptr[i*2]).value.decode('utf-8')
                freq = int(ctypes.c_char_p(words_ptr[i*2+1]).value.decode('utf-8'))
                results.append((word, freq))
            self.lib.lekhika_free_words(words_ptr, count * 2)
        return results
