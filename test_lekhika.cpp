#include "src/lekhika_wrapper.cpp"
#include <iostream>

int main() {
    std::cout << "Creating context..." << std::endl;
    LekhikaContext* ctx = lekhika_create("data", "/home/computebox/.local/share/lekhika-core/lekhikadict.akshardb");
    if (!ctx) {
        std::cerr << "Failed to create context" << std::endl;
        return 1;
    }
    std::cout << "Transliterating..." << std::endl;
    char* res = lekhika_transliterate(ctx, "namaste");
    if (res) {
        std::cout << "Result: " << res << std::endl;
        lekhika_free_string(res);
    } else {
        std::cerr << "Transliteration failed" << std::endl;
    }
    lekhika_destroy(ctx);
    return 0;
}
