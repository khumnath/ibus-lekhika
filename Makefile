CXX = g++
CXXFLAGS = -O3 -Wall -fPIC -std=c++17 -DHAVE_SQLITE3
LDFLAGS = -shared -Wl,-rpath,'$$ORIGIN'

# Support building in a separate directory
BUILD_DIR ?= .
CORE_DIR ?= $(CURDIR)/liblekhika

INCLUDES = -I$(CORE_DIR)/core/include $(shell pkg-config --cflags icu-uc sqlite3)
LIBS = -L$(CORE_DIR)/build/core -l:liblekhika.so $(shell pkg-config --libs icu-uc sqlite3)

TARGET = $(BUILD_DIR)/ibus-lekhika.so
SRC = src/lekhika_wrapper.cpp

all: prepare $(TARGET)

prepare:
	mkdir -p $(BUILD_DIR)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) $(INCLUDES) -shared -o $@ $^ $(LIBS) -Wl,-rpath,'$$ORIGIN'

clean:
	rm -f $(TARGET)
