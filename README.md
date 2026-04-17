# IBus Lekhika: Nepali Transliteration Input Method

IBus Lekhika is a professional-grade Nepali transliteration engine for Linux. It allows you to type Nepali naturally using a standard QWERTY keyboard by converting romanized words into Devnagari in real-time.

## Project Structure

This project is a hybrid integration of a high-performance C++ core and a flexible Python-based IBus engine.

### 1. [liblekhika](https://github.com/khumnath/liblekhika) (The Core)
The engine's heart is the [liblekhika](https://github.com/khumnath/liblekhika) library. It handles:
- **Transliteration Logic**: Complex rule-based mapping from Roman characters to Devnagari.
- **Dictionary Management**: Efficient word lookups using SQLite3.
- **Unicode Processing**: Precise character handling powered by ICU (International Components for Unicode).

### 2. IBus Wrapper & Engine
The wrapper layer bridges the C++ core to the Linux desktop environment:
- **C++ Wrapper**: A C-compatible interface (`lekhika_wrapper.cpp`) that exposes the engine's functionality to high-level languages.
- **Python Bridge**: Uses `ctypes` to interface with the shared library.
- **IBus Engine**: A Python-based service (`engine.py`) that manages the GObject loop, preedit strings, and candidate window interactions.

## Quick Start (Build & Install)

We provide an automated, multi-distribution setup script that handles dependency installation, compilation, and system registration in one step.

```bash
# Clone the repository
git clone https://github.com/khumnath/ibus-lekhika.git
cd ibus-lekhika

# Run the automated installer
chmod +x build-and-install.sh
./build-and-install.sh
```

### Supported Distributions
The installer automatically detects and configures:
- **Debian / Ubuntu / Mint**: Uses `apt` and `im-config`.
- **Fedora**: Uses `dnf` and `imsettings`.
- **Arch Linux**: Uses `pacman`.

## Architecture Details

- **Language Logic**: Written in C++ for maximum throughput and low latency during typing.
- **Isolation**: The project uses a "kitchen" build strategy, isolating external dependencies and build artifacts from the source tree.
- **User-Centric Deployment**: core files are installed to `~/.local/lib/ibus-lekhika/`, ensuring your system remains clean and the input method is portable.

## Configuration

After installation, the "Lekhika (Nepali)" engine should automatically appear in your IBus active engines. You can cycle to it using your configured IBus shortcut (usually `Super + Space`).

To customize dictionary behavior or word pairs, refer to the files in `~/.local/lib/ibus-lekhika/data/`.

## License
This project is licensed under the GPL License.
