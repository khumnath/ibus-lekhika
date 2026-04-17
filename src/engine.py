#!/usr/bin/python3
import gi
gi.require_version('IBus', '1.0')
from gi.repository import IBus, GLib
import sys
import os
import logging
import traceback
import subprocess
from datetime import datetime
from lekhika_wrap import LekhikaWrapper
import config_manager

# Setup logging
log_file = os.path.expanduser("~/.cache/ibus-lekhika.log")
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("Starting Lekhika Engine")

# Path Configuration
LIB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ibus-lekhika.so")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

class LekhikaEngine(IBus.Engine):
    def __init__(self):
        super(LekhikaEngine, self).__init__()
        
        # Load persistent settings
        self.settings = config_manager.load_config()
        
        # Initialize Lekhika Core
        dict_path = self.settings.get("dictionary_path", "")
        if not dict_path or not os.path.exists(dict_path):
            dict_path = os.path.expanduser("~/.local/share/lekhika-core/lekhikadict.akshardb")

        try:
            self.lekhika = LekhikaWrapper(LIB_PATH, DATA_DIR, dict_path)
            self.apply_settings()
            logging.info(f"Lekhika initialized with LIB: {LIB_PATH}, DICT: {dict_path}")
        except Exception as e:
            logging.error(f"Error initializing Lekhika: {e}")
            sys.exit(1)
            
        self.buffer = ""
        self.cursor_pos = 0
        self.table = IBus.LookupTable.new(10, 0, True, True)
        self.table.set_orientation(IBus.Orientation.VERTICAL)
        
        # Explicitly update properties on init
        self.update_property_list()

    def do_process_key_event(self, keyval, keycode, state):
        try:
            if state & IBus.ModifierType.RELEASE_MASK: return False
            if state & (IBus.ModifierType.CONTROL_MASK | IBus.ModifierType.MOD1_MASK | IBus.ModifierType.SUPER_MASK): return False

            if keyval == IBus.KEY_BackSpace:
                if len(self.buffer) > 0 and self.cursor_pos > 0:
                    self.buffer = self.buffer[:self.cursor_pos-1] + self.buffer[self.cursor_pos:]
                    self.cursor_pos -= 1
                    self.update_preedit()
                    return True
                return False

            if self.buffer and IBus.KEY_1 <= keyval <= IBus.KEY_9:
                if self.select_candidate(keyval - IBus.KEY_1): return True

            if keyval == IBus.KEY_space:
                if self.buffer:
                    if self.settings.get("space_commits_suggestion", False):
                        if self.select_candidate(self.table.get_cursor_pos()): return True
                    res = self.lekhika.transliterate(self.buffer)
                    self.commit_text(IBus.Text.new_from_string(res + " "))
                    self.lekhika.add_word(res)
                    self.reset_state()
                    return True 
                return False

            if keyval == IBus.KEY_Return:
                if self.buffer:
                    if self.select_candidate(self.table.get_cursor_pos()): return True
                    res = self.lekhika.transliterate(self.buffer)
                    self.commit_text(IBus.Text.new_from_string(res)) # No extra space on Enter if no table
                    self.lekhika.add_word(res)
                    self.reset_state()
                    return True
                return False

            if keyval == IBus.KEY_Escape:
                if self.buffer:
                    # Escape commits RAW buffer
                    self.commit_text(IBus.Text.new_from_string(self.buffer))
                    self.reset_state()
                    return True
                return False

            if keyval in (IBus.KEY_Page_Up, IBus.KEY_KP_Page_Up):
                if self.buffer and self.table.get_number_of_candidates() > 0:
                    self.table.page_up(); self.update_lookup_table(self.table, True); return True
                return False
            if keyval in (IBus.KEY_Page_Down, IBus.KEY_KP_Page_Down):
                if self.buffer and self.table.get_number_of_candidates() > 0:
                    self.table.page_down(); self.update_lookup_table(self.table, True); return True
                return False
            if keyval in (IBus.KEY_Up, IBus.KEY_KP_Up):
                if self.buffer and self.table.get_number_of_candidates() > 0:
                    self.table.cursor_up(); self.update_lookup_table(self.table, True); return True
                return False
            if keyval in (IBus.KEY_Down, IBus.KEY_KP_Down):
                if self.buffer and self.table.get_number_of_candidates() > 0:
                    self.table.cursor_down(); self.update_lookup_table(self.table, True); return True
                return False

            if keyval in (IBus.KEY_Left, IBus.KEY_KP_Left):
                if self.buffer and self.cursor_pos > 0:
                    self.cursor_pos -= 1; self.update_preedit(); return True
                return False
            if keyval in (IBus.KEY_Right, IBus.KEY_KP_Right):
                if self.buffer and self.cursor_pos < len(self.buffer):
                    self.cursor_pos += 1; self.update_preedit(); return True
                return False

            c = IBus.keyval_to_unicode(keyval)
            if c:
                syms = "!@#$%^()-_=+[]{};:'\",.<>?|\\"
                if c == "/" or c in syms or (c.isdigit() and not self.buffer):
                    self.commit_buffer()
                    res = self.lekhika.transliterate(c)
                    self.commit_text(IBus.Text.new_from_string(res))
                    return True
                if c.isalnum() or c in "*#":
                    self.buffer = self.buffer[:self.cursor_pos] + c + self.buffer[self.cursor_pos:]
                    self.cursor_pos += 1; self.update_preedit(); return True
                self.commit_buffer()
        except: logging.error(traceback.format_exc())
        return False

    def select_candidate(self, index):
        if self.table and self.table.get_number_of_candidates() > index:
            word = self.table.get_candidate(index).get_text()
            self.commit_text(IBus.Text.new_from_string(word + " "))
            self.lekhika.add_word(word); self.reset_state(); return True
        return False

    def commit_buffer(self):
        if self.buffer:
            res = self.lekhika.transliterate(self.buffer)
            self.commit_text(IBus.Text.new_from_string(res))
            self.lekhika.add_word(res); self.reset_state()

    def reset_state(self):
        self.buffer = ""; self.cursor_pos = 0; self.update_preedit()

    def update_preedit(self):
        try:
            text = IBus.Text.new_from_string("")
            if self.buffer:
                res = self.lekhika.transliterate(self.buffer)
                disp = f"{self.buffer} ⇾ {res}"
                text = IBus.Text.new_from_string(disp)
                text.append_attribute(IBus.AttrType.UNDERLINE, 1, 0, len(self.buffer))
                text.append_attribute(IBus.AttrType.FOREGROUND, 0x888888, len(self.buffer), len(disp))
                self.update_preedit_text(text, self.cursor_pos, True)
                self.update_candidates(res)
            else:
                self.update_preedit_text(text, 0, False)
                self.hide_lookup_table()
        except: logging.error(f"Error in update_preedit: {traceback.format_exc()}")

    def update_candidates(self, prefix):
        if not self.settings.get("enable_suggestions", True):
            self.hide_lookup_table(); return
        words = self.lekhika.find_words(prefix, 9)
        if words:
            self.table.clear()
            for w in words: self.table.append_candidate(IBus.Text.new_from_string(w))
            self.update_lookup_table(self.table, True)
        else: self.hide_lookup_table()

    def do_focus_in(self):
        self.settings = config_manager.load_config()
        self.apply_settings()
        self.update_property_list()

    def do_focus_out(self): self.commit_buffer()

    def apply_settings(self):
        self.lekhika.set_options(
            smart=self.settings.get("smart_correction", True),
            auto=self.settings.get("auto_correct", True),
            numbers=self.settings.get("indic_numbers", True),
            symbols=self.settings.get("symbols_translit", True)
        )

    def do_property_activate(self, prop_name, state):
        logging.info(f"Property activated: {prop_name}")
        
        if prop_name in ["setup", "idx_configure"]:
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup.py")
            logging.info(f"Launching configuration utility: {script}")
            try:
                env = os.environ.copy()
                with open(log_file, "a") as f:
                    f.write(f"\n--- Launching setup.py at {datetime.now().isoformat()} ---\n")
                    subprocess.Popen([sys.executable, script], env=env, stdout=f, stderr=f)
            except Exception as e:
                logging.error(f"Failed to launch configuration: {e}")
            return

        if prop_name in self.settings:
            self.settings[prop_name] = not self.settings[prop_name]
            config_manager.save_config(self.settings)
            self.apply_settings()
            self.update_property_list()

    def update_property_list(self):
        try:
            logging.debug("Starting update_property_list...")
            prop_list = IBus.PropList()
            empty_text = IBus.Text.new_from_string("")
            
            # Header anchor
            header_prop = IBus.Property.new(
                "idx_header", IBus.PropType.MENU,
                IBus.Text.new_from_string("Lekhika Settings"),
                "help-about", empty_text, True, True, 
                IBus.PropState.UNCHECKED, None
            )
            prop_list.append(header_prop)

            # Configuration link
            config_prop = IBus.Property.new(
                "setup", IBus.PropType.NORMAL,
                IBus.Text.new_from_string("Open Configuration..."),
                "preferences-system-symbolic", empty_text, 
                True, True, IBus.PropState.UNCHECKED, None
            )
            prop_list.append(config_prop)

            def create_toggle(id, label, active):
                return IBus.Property.new(
                    id, IBus.PropType.TOGGLE,
                    IBus.Text.new_from_string(label),
                    "gtk-apply", empty_text, True, True,
                    IBus.PropState.CHECKED if active else IBus.PropState.UNCHECKED,
                    None
                )

            prop_list.append(create_toggle("smart_correction", "Smart Correction", self.settings.get("smart_correction", True)))
            prop_list.append(create_toggle("auto_correct", "Auto Correct", self.settings.get("auto_correct", True)))
            prop_list.append(create_toggle("indic_numbers", "Indic Numbers", self.settings.get("indic_numbers", True)))
            prop_list.append(create_toggle("symbols_translit", "Symbols Transliteration", self.settings.get("symbols_translit", True)))
            prop_list.append(create_toggle("space_commits_suggestion", "Space commits selected suggestion", self.settings.get("space_commits_suggestion", True)))
            prop_list.append(create_toggle("enable_suggestions", "Word Suggestions", self.settings.get("enable_suggestions", True)))
            
            self.register_properties(prop_list)
            logging.debug("Properties registered successfully")
            
        except Exception as e:
            logging.error(f"Error in update_property_list: {traceback.format_exc()}")

    def do_activate(self):
        logging.info("Engine activated")
        self.update_property_list()

class LekhikaComponent:
    def __init__(self):
        self.bus = IBus.Bus()
        self.factory = IBus.Factory.new(self.bus.get_connection())
        self.factory.add_engine("lekhika", LekhikaEngine)
        self.bus.request_name("org.freedesktop.IBus.Lekhika", 0)
        
    def run(self):
        GLib.MainLoop().run()

if __name__ == "__main__":
    IBus.init()
    LekhikaComponent().run()
