#!/usr/bin/python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import os
import sys
import json
import config_manager
import subprocess
import re
import threading
from lekhika_wrap import LekhikaWrapper

# Path Configuration
LIB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ibus-lekhika.so")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

class LekhikaSetup:
    def __init__(self):
        self.window = Gtk.Window(title="Lekhika Configuration")
        self.window.set_default_size(700, 550)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("destroy", Gtk.main_quit)

        # Load current config
        self.config = config_manager.load_config()
        
        # Initialize Lekhika for dictionary access
        db_path = self.config.get("dictionary_path", "")
        if not db_path or not os.path.exists(db_path):
            db_path = os.path.expanduser("~/.local/share/lekhika-core/lekhikadict.akshardb")
        
        try:
            self.lekhika = LekhikaWrapper(LIB_PATH, DATA_DIR, db_path)
        except Exception as e:
            print(f"Warning: Could not init LekhikaWrapper: {e}")
            self.lekhika = None

        self.autocorrect_file = os.path.join(DATA_DIR, "autocorrect.toml")

        # Root Layout: Notebook for Tabs
        self.notebook = Gtk.Notebook()
        self.window.add(self.notebook)

        # Tab 1: General Settings
        self.settings_tab = self.create_settings_tab()
        self.notebook.append_page(self.settings_tab, Gtk.Label(label="General Settings"))

        # Tab 2: Dictionary Manager
        self.dict_tab = self.create_dictionary_tab()
        self.notebook.append_page(self.dict_tab, Gtk.Label(label="Dictionary Manager"))

        # Tab 3: Roman Mappings (Autocorrect)
        self.mappings_tab = self.create_mappings_tab()
        self.notebook.append_page(self.mappings_tab, Gtk.Label(label="Roman Mappings"))

        self.window.show_all()

    def create_settings_tab(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(20)
        vbox.set_margin_start(20)
        vbox.set_margin_end(20)

        # Engine Settings Frame
        settings_frame = Gtk.Frame(label="Engine Behavior")
        settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        settings_box.set_margin_top(10)
        settings_box.set_margin_bottom(10)
        settings_box.set_margin_start(10)
        settings_box.set_margin_end(10)
        settings_frame.add(settings_box)
        vbox.pack_start(settings_frame, False, False, 0)

        self.smart_toggle = Gtk.CheckButton(label="Enable Smart Correction")
        self.smart_toggle.set_active(self.config.get("smart_correction", True))
        settings_box.pack_start(self.smart_toggle, False, False, 0)

        self.auto_toggle = Gtk.CheckButton(label="Enable Auto Correct")
        self.auto_toggle.set_active(self.config.get("auto_correct", True))
        settings_box.pack_start(self.auto_toggle, False, False, 0)

        self.num_toggle = Gtk.CheckButton(label="Transliterate Numbers to Indic Numeral")
        self.num_toggle.set_active(self.config.get("indic_numbers", True))
        settings_box.pack_start(self.num_toggle, False, False, 0)

        self.suggest_toggle = Gtk.CheckButton(label="Enable Word Suggestions")
        self.suggest_toggle.set_active(self.config.get("enable_suggestions", True))
        settings_box.pack_start(self.suggest_toggle, False, False, 0)

        self.space_toggle = Gtk.CheckButton(label="Space key commits selected suggestion")
        self.space_toggle.set_active(self.config.get("space_commits_suggestion", True))
        settings_box.pack_start(self.space_toggle, False, False, 0)

        # Dictionary Path Frame
        dict_frame = Gtk.Frame(label="Database Location")
        dict_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        dict_box.set_margin_top(10)
        dict_box.set_margin_bottom(10)
        dict_box.set_margin_start(10)
        dict_box.set_margin_end(10)
        dict_frame.add(dict_box)
        vbox.pack_start(dict_frame, False, False, 0)

        path_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.dict_entry = Gtk.Entry()
        self.dict_entry.set_text(self.config.get("dictionary_path", ""))
        path_hbox.pack_start(self.dict_entry, True, True, 0)

        browse_btn = Gtk.Button(label="Browse...")
        browse_btn.connect("clicked", self.on_browse)
        path_hbox.pack_start(browse_btn, False, False, 0)
        dict_box.pack_start(path_hbox, False, False, 0)

        # Action Buttons
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        save_btn = Gtk.Button(label="Apply Changes")
        save_btn.get_style_context().add_class("suggested-action")
        save_btn.connect("clicked", self.on_save)
        footer.pack_end(save_btn, False, False, 0)
        vbox.pack_end(footer, False, False, 0)

        return vbox

    def create_dictionary_tab(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)

        # Info Area
        self.status_label = Gtk.Label(label="Manage your personal dictionary database.")
        self.status_label.set_alignment(0, 0.5)
        vbox.pack_start(self.status_label, False, False, 0)

        # Top Controls: Search and Add
        top_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search words (Latin or Devanagari)...")
        self.search_entry.connect("activate", self.on_search)
        top_hbox.pack_start(self.search_entry, True, True, 0)
        
        search_btn = Gtk.Button(label="Search")
        search_btn.connect("clicked", self.on_search)
        top_hbox.pack_start(search_btn, False, False, 0)
        
        add_btn = Gtk.Button(label="Add Word")
        add_btn.connect("clicked", self.on_add_word_dialog)
        top_hbox.pack_start(add_btn, False, False, 0)
        vbox.pack_start(top_hbox, False, False, 0)

        # Word List (TreeView)
        self.store = Gtk.ListStore(str, int) # Word, Frequency
        self.treeview = Gtk.TreeView(model=self.store)
        
        renderer_text = Gtk.CellRendererText()
        column_word = Gtk.TreeViewColumn("Nepali Word", renderer_text, text=0)
        column_word.set_resizable(True)
        column_word.set_expand(True)
        column_word.set_sort_column_id(0)
        self.treeview.append_column(column_word)
        
        renderer_freq = Gtk.CellRendererText()
        column_freq = Gtk.TreeViewColumn("Frequency", renderer_freq, text=1)
        column_freq.set_sort_column_id(1)
        column_freq.set_min_width(100)
        self.treeview.append_column(column_freq)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.add(self.treeview)
        vbox.pack_start(scrolled_window, True, True, 0)

        # Bottom Controls: Bulk Actions
        bottom_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.load_more_btn = Gtk.Button(label="Load More...")
        self.load_more_btn.connect("clicked", self.on_load_more)
        bottom_hbox.pack_start(self.load_more_btn, False, False, 0)
        
        bottom_hbox.add(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        learn_btn = Gtk.Button(label="Learn from File...")
        learn_btn.connect("clicked", self.on_learn_from_file)
        bottom_hbox.pack_start(learn_btn, False, False, 0)

        del_btn = Gtk.Button(label="Delete Selected")
        del_btn.get_style_context().add_class("destructive-action")
        del_btn.connect("clicked", self.on_delete_word)
        bottom_hbox.pack_start(del_btn, False, False, 0)

        reset_btn = Gtk.Button(label="Reset DB")
        reset_btn.get_style_context().add_class("destructive-action")
        reset_btn.connect("clicked", self.on_reset_db)
        bottom_hbox.pack_end(reset_btn, False, False, 0)

        refresh_btn = Gtk.Button(label="Reload")
        refresh_btn.connect("clicked", self.on_refresh_dict)
        bottom_hbox.pack_end(refresh_btn, False, False, 0)
        
        vbox.pack_start(bottom_hbox, False, False, 0)

        # Initial Load
        self.offset = 0
        self.page_size = 50
        self.on_refresh_dict(None)

        return vbox

    def create_mappings_tab(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)

        # Info Area
        info_label = Gtk.Label(label="Manage explicit Roman-to-Devanagari mappings (autocorrect.toml).")
        info_label.set_alignment(0, 0.5)
        vbox.pack_start(info_label, False, False, 0)

        # Top Controls
        top_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_mapping_btn = Gtk.Button(label="Add Mapping")
        add_mapping_btn.connect("clicked", self.on_add_mapping_dialog)
        top_hbox.pack_start(add_mapping_btn, False, False, 0)
        
        learn_mapping_btn = Gtk.Button(label="Learn from Mapping File...")
        learn_mapping_btn.connect("clicked", self.on_learn_mappings_from_file)
        top_hbox.pack_start(learn_mapping_btn, False, False, 0)
        
        vbox.pack_start(top_hbox, False, False, 0)

        # Mappings List (TreeView)
        self.mapping_store = Gtk.ListStore(str, str) # Roman, Devanagari
        self.mapping_treeview = Gtk.TreeView(model=self.mapping_store)
        
        renderer_roman = Gtk.CellRendererText()
        column_roman = Gtk.TreeViewColumn("Roman Input", renderer_roman, text=0)
        column_roman.set_resizable(True)
        column_roman.set_expand(True)
        column_roman.set_sort_column_id(0)
        self.mapping_treeview.append_column(column_roman)
        
        renderer_dev = Gtk.CellRendererText()
        column_dev = Gtk.TreeViewColumn("Devanagari Output", renderer_dev, text=1)
        column_dev.set_resizable(True)
        column_dev.set_expand(True)
        column_dev.set_sort_column_id(1)
        self.mapping_treeview.append_column(column_dev)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.add(self.mapping_treeview)
        vbox.pack_start(scrolled_window, True, True, 0)

        # Bottom Controls
        bottom_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        del_mapping_btn = Gtk.Button(label="Delete Selected")
        del_mapping_btn.get_style_context().add_class("destructive-action")
        del_mapping_btn.connect("clicked", self.on_delete_mapping)
        bottom_hbox.pack_start(del_mapping_btn, False, False, 0)
        
        refresh_mapping_btn = Gtk.Button(label="Reload Mappings")
        refresh_mapping_btn.connect("clicked", self.on_refresh_mappings)
        bottom_hbox.pack_end(refresh_mapping_btn, False, False, 0)
        
        vbox.pack_start(bottom_hbox, False, False, 0)

        # Initial Load
        self.on_refresh_mappings(None)

        return vbox

    # Autocorrect TOML Handlers
    def load_autocorrect_mappings(self):
        mappings = []
        if not os.path.exists(self.autocorrect_file):
            return mappings
        
        try:
            with open(self.autocorrect_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            in_special_words = False
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'): continue
                
                if line.startswith('[') and line.endswith(']'):
                    section = line[1:-1].strip()
                    in_special_words = (section == "specialWords")
                    continue
                
                if in_special_words and '=' in line:
                    parts = line.split('=', 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                    if val.startswith('"') and val.endswith('"'):
                        val = val[1:-1]
                    elif val.startswith("'") and val.endswith("'"):
                        val = val[1:-1]
                    mappings.append((key, val))
        except Exception as e:
            print(f"Error loading mappings: {e}")
        
        return mappings

    def save_autocorrect_mapping(self, roman, devanagari):
        if not os.path.exists(self.autocorrect_file):
            # Create basic structure if missing
            with open(self.autocorrect_file, 'w', encoding='utf-8') as f:
                f.write("[specialWords]\n")
        
        try:
            with open(self.autocorrect_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            found_section = False
            replaced = False
            
            for line in lines:
                stripped = line.strip()
                if stripped == "[specialWords]":
                    found_section = True
                    new_lines.append(line)
                    continue
                
                if found_section and not replaced and '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    if key == roman:
                        new_lines.append(f'{roman} = "{devanagari}"\n')
                        replaced = True
                        continue
                
                # If we hit another section, and haven't added our key yet, add it
                if found_section and not replaced and stripped.startswith('[') and stripped.endswith(']'):
                    new_lines.append(f'{roman} = "{devanagari}"\n\n')
                    replaced = True
                
                new_lines.append(line)
            
            if found_section and not replaced:
                new_lines.append(f'{roman} = "{devanagari}"\n')
            elif not found_section:
                new_lines.append("\n[specialWords]\n")
                new_lines.append(f'{roman} = "{devanagari}"\n')
            
            with open(self.autocorrect_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            return True
        except Exception as e:
            print(f"Error saving mapping: {e}")
            return False

    def remove_autocorrect_mapping(self, roman):
        if not os.path.exists(self.autocorrect_file): return False
        
        try:
            with open(self.autocorrect_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            in_special_words = False
            for line in lines:
                stripped = line.strip()
                if stripped == "[specialWords]":
                    in_special_words = True
                    new_lines.append(line)
                    continue
                
                if in_special_words and '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    if key == roman:
                        continue # Skip this line
                
                if in_special_words and stripped.startswith('[') and stripped.endswith(']'):
                    in_special_words = False
                
                new_lines.append(line)
            
            with open(self.autocorrect_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        except Exception as e:
            print(f"Error removing mapping: {e}")
            return False

    def on_refresh_mappings(self, button):
        self.mapping_store.clear()
        mappings = self.load_autocorrect_mappings()
        for roman, dev in mappings:
            self.mapping_store.append([roman, dev])

    def on_add_mapping_dialog(self, button):
        dialog = Gtk.Dialog(title="Add Roman Mapping", parent=self.window, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        
        area = dialog.get_content_area()
        grid = Gtk.Grid(column_spacing=10, row_spacing=10)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_margin_start(10)
        grid.set_margin_end(10)
        
        grid.attach(Gtk.Label(label="Roman Input:"), 0, 0, 1, 1)
        roman_entry = Gtk.Entry()
        grid.attach(roman_entry, 1, 0, 1, 1)
        
        grid.attach(Gtk.Label(label="Devanagari Output:"), 0, 1, 1, 1)
        dev_entry = Gtk.Entry()
        grid.attach(dev_entry, 1, 1, 1, 1)
        
        area.add(grid)
        dialog.show_all()
        
        if dialog.run() == Gtk.ResponseType.OK:
            roman = roman_entry.get_text().strip()
            dev = dev_entry.get_text().strip()
            if roman and dev:
                self.save_autocorrect_mapping(roman, dev)
                self.on_refresh_mappings(None)
        dialog.destroy()

    def on_delete_mapping(self, button):
        selection = self.mapping_treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            roman = model[treeiter][0]
            confirm = Gtk.MessageDialog(parent=self.window, flags=0, message_type=Gtk.MessageType.QUESTION,
                                        buttons=Gtk.ButtonsType.YES_NO, text=f"Remove mapping for '{roman}'?")
            if confirm.run() == Gtk.ResponseType.YES:
                self.remove_autocorrect_mapping(roman)
                self.on_refresh_mappings(None)
            confirm.destroy()

    def on_learn_mappings_from_file(self, button):
        dialog = Gtk.FileChooserDialog(title="Choose Mapping File (roman -> devanagari)", parent=self.window, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        
        res = dialog.run()
        if res == Gtk.ResponseType.OK:
            path = dialog.get_filename()
            dialog.destroy()
            self.start_learning_mappings(path)
        else:
            dialog.destroy()

    def start_learning_mappings(self, path):
        try:
            count = 0
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'): continue
                    
                    if '->' in line:
                        parts = line.split('->', 1)
                        roman = parts[0].strip()
                        dev = parts[1].strip()
                        if roman and dev:
                            self.save_autocorrect_mapping(roman, dev)
                            count += 1
                    elif '=' in line:
                        parts = line.split('=', 1)
                        roman = parts[0].strip()
                        dev = parts[1].strip()
                        if dev.startswith('"') and dev.endswith('"'): dev = dev[1:-1]
                        if roman and dev:
                            self.save_autocorrect_mapping(roman, dev)
                            count += 1
            
            message = Gtk.MessageDialog(parent=self.window, flags=0, message_type=Gtk.MessageType.INFO,
                                        buttons=Gtk.ButtonsType.OK, text=f"Learned {count} mappings from file.")
            message.run()
            message.destroy()
            self.on_refresh_mappings(None)
        except Exception as e:
            error_dialog = Gtk.MessageDialog(parent=self.window, flags=0, message_type=Gtk.MessageType.ERROR,
                                             buttons=Gtk.ButtonsType.OK, text=f"Failed to learn mappings: {e}")
            error_dialog.run()
            error_dialog.destroy()

    # Handlers
    def on_browse(self, button):
        dialog = Gtk.FileChooserDialog(title="Select Dictionary", parent=self.window, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        res = dialog.run()
        if res == Gtk.ResponseType.OK:
            self.dict_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def on_save(self, button):
        self.config["smart_correction"] = self.smart_toggle.get_active()
        self.config["auto_correct"] = self.auto_toggle.get_active()
        self.config["indic_numbers"] = self.num_toggle.get_active()
        self.config["enable_suggestions"] = self.suggest_toggle.get_active()
        self.config["space_commits_suggestion"] = self.space_toggle.get_active()
        self.config["dictionary_path"] = self.dict_entry.get_text()
        config_manager.save_config(self.config)
        subprocess.Popen(["ibus", "restart"])
        Gtk.main_quit()

    def on_refresh_dict(self, button):
        self.store.clear()
        self.offset = 0
        self.load_words()

    def load_words(self):
        if not self.lekhika: return
        words = self.lekhika.get_all_words(limit=self.page_size, offset=self.offset)
        for word, freq in words:
            self.store.append([word, freq])
        self.offset += len(words)
        self.load_more_btn.set_sensitive(len(words) == self.page_size)

    def on_load_more(self, button):
        self.load_words()

    def on_search(self, widget):
        if not self.lekhika: return
        query = self.search_entry.get_text()
        if not query:
            self.on_refresh_dict(None)
            return
        
        self.store.clear()
        # Transliterate query first if it might be Latin
        dev_query = self.lekhika.transliterate(query)
        results = self.lekhika.search_words(dev_query)
        for word, freq in results:
            self.store.append([word, freq])
        self.load_more_btn.set_sensitive(False)

    def on_add_word_dialog(self, button):
        dialog = Gtk.MessageDialog(parent=self.window, flags=0, message_type=Gtk.MessageType.OTHER,
                                   buttons=Gtk.ButtonsType.OK_CANCEL, text="Enter a new Nepali word:")
        entry = Gtk.Entry()
        dialog.get_content_area().pack_start(entry, True, True, 0)
        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            word = entry.get_text().strip()
            if word:
                self.lekhika.add_word(word)
                self.on_refresh_dict(None)
        dialog.destroy()

    def on_delete_word(self, button):
        if not self.lekhika: return
        selection = self.treeview.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            word = model[treeiter][0]
            confirm = Gtk.MessageDialog(parent=self.window, flags=0, message_type=Gtk.MessageType.QUESTION,
                                        buttons=Gtk.ButtonsType.YES_NO, text=f"Delete word '{word}'?")
            if confirm.run() == Gtk.ResponseType.YES:
                self.lekhika.remove_word(word)
                model.remove(treeiter)
            confirm.destroy()

    def on_reset_db(self, button):
        confirm = Gtk.MessageDialog(parent=self.window, flags=0, message_type=Gtk.MessageType.WARNING,
                                    buttons=Gtk.ButtonsType.YES_NO, 
                                    text="Wipe entire dictionary database? This cannot be undone.")
        if confirm.run() == Gtk.ResponseType.YES:
            self.lekhika.reset_dictionary()
            self.on_refresh_dict(None)
        confirm.destroy()

    def on_learn_from_file(self, button):
        dialog = Gtk.FileChooserDialog(title="Choose Text File to Learn From", parent=self.window, action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)
        
        res = dialog.run()
        if res == Gtk.ResponseType.OK:
            path = dialog.get_filename()
            dialog.destroy()
            self.start_learning(path)
        else:
            dialog.destroy()

    def start_learning(self, path):
        self.status_label.set_text("Learning from file. Please wait...")
        threading.Thread(target=self.learning_thread, args=(path,), daemon=True).start()

    def learning_thread(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Devanagari word extraction logic
            words = re.findall(r'[\u0900-\u097F]+', content)
            unique_words = set(words)
            
            count = 0
            for word in unique_words:
                self.lekhika.add_word(word)
                count += 1
            
            GLib.idle_add(self.finish_learning, count)
        except Exception as e:
            GLib.idle_add(self.status_label.set_text, f"Learning failed: {e}")

    def finish_learning(self, count):
        self.status_label.set_text(f"Successfully learned {count} unique words from file.")
        self.on_refresh_dict(None)

if __name__ == "__main__":
    LekhikaSetup()
    Gtk.main()
