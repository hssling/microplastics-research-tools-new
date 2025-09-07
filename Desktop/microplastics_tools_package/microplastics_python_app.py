"""
Microplastics Systematic Review Data Extraction Tool
====================================================

A comprehensive Python application for extracting and managing data 
for systematic reviews on microplastics research.

Requirements:
pip install pandas tkinter openpyxl

Usage:
python microplastics_data_extraction.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import json
import os
from datetime import datetime
import re

class MicroplasticsDataExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Microplastics Systematic Review Data Extraction Tool")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f0f0')
        
        # Data storage
        self.data = []
        self.current_row = 0
        
        # Initialize sample data
        self.initialize_sample_data()
        
        # Create GUI
        self.create_widgets()
        self.populate_tree()
        
    def initialize_sample_data(self):
        """Initialize with sample articles from the provided list"""
        sample_data = [
            {
                'ID': 1,
                'First_Author': 'Abimbola I',
                'Year': 2024,
                'Title': 'In-situ detection of microplastics in the aquatic environment: A systematic literature review',
                'Journal': 'Sci Total Environ',
                'Study_Type': 'Systematic Review',
                'Research_Focus': 'Detection Methods',
                'Environment': 'Aquatic',
                'Organisms': '',
                'Sample_Size': '',
                'MP_Detection_Method': 'Various in-situ methods',
                'MP_Concentration': '',
                'MP_Size_Range': '',
                'MP_Type': '',
                'Exposure_Route': '',
                'Exposure_Duration': '',
                'Health_Effects': '',
                'Toxicity_Endpoints': '',
                'Geographic_Location': '',
                'Key_Findings': '',
                'Study_Limitations': '',
                'Quality_Score': '',
                'Risk_of_Bias': '',
                'Full_Citation': 'Abimbola I, McAfee M, Creedon L, Gharbia S. In-situ detection of microplastics in the aquatic environment: A systematic literature review. Sci Total Environ. 2024;934:173111.',
                'Notes': '',
                'Date_Extracted': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'ID': 2,
                'First_Author': 'Ali-Hassanzadeh M',
                'Year': 2025,
                'Title': 'The effects of exposure to microplastics on female reproductive health and pregnancy outcomes: A systematic review and meta-analysis',
                'Journal': 'Reprod Toxicol',
                'Study_Type': 'Systematic Review & Meta-analysis',
                'Research_Focus': 'Reproductive Health',
                'Environment': '',
                'Organisms': 'Humans - Female',
                'Sample_Size': '',
                'MP_Detection_Method': '',
                'MP_Concentration': '',
                'MP_Size_Range': '',
                'MP_Type': '',
                'Exposure_Route': '',
                'Exposure_Duration': '',
                'Health_Effects': 'Reproductive health effects, pregnancy outcomes',
                'Toxicity_Endpoints': 'Reproductive toxicity',
                'Geographic_Location': '',
                'Key_Findings': '',
                'Study_Limitations': '',
                'Quality_Score': '',
                'Risk_of_Bias': '',
                'Full_Citation': 'Ali-Hassanzadeh M, Arefinia N, Ghoreshi ZA, Askarpour H, Mashayekhi-Sardoo H. The effects of exposure to microplastics on female reproductive health and pregnancy outcomes: A systematic review and meta-analysis. Reprod Toxicol. 2025;135:108932.',
                'Notes': '',
                'Date_Extracted': datetime.now().strftime('%Y-%m-%d')
            }
        ]
        self.data = sample_data
        
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="🔬 Microplastics Systematic Review Data Extraction", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))

        ttk.Button(control_frame, text="➕ Add New Article", command=self.add_new_article).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="📝 Edit Selected", command=self.edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🗑️ Delete Selected", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="💾 Save to Excel", command=self.save_to_excel).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="💾 Save to CSV", command=self.save_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📂 Load from File", command=self.load_from_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📥 Import References", command=self.import_references).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🧹 Deduplicate", command=self.deduplicate_references).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📊 PRISMA Export", command=self.export_prisma).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📝 Bulk Screening", command=self.bulk_screening).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="📎 Attach PDF", command=self.attach_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔎 Advanced Filter", command=self.advanced_filter_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🏷️ Tag Selected", command=self.tag_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="💬 Add Note", command=self.add_note_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⬇️ Export Subset", command=self.export_subset).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔗 Link References", command=self.link_references).pack(side=tk.LEFT, padx=5)

        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=1, column=0, columnspan=3, pady=(30, 10), sticky=(tk.W, tk.E))

        ttk.Label(search_frame, text="🔍 Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_data)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)

        # Treeview for displaying data
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Define columns
        columns = ('ID', 'Author', 'Year', 'Title', 'Journal', 'Study_Type', 'Research_Focus', 'Screening_Status', 'Tags', 'Notes', 'PDF', 'Linked_IDs', 'Audit_Trail')

        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)

        # Define headings
        for col in columns:
            self.tree.heading(col, text=col.replace('_', ' '))
            self.tree.column(col, width=120, minwidth=80)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid scrollbars and tree
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set(f"Total Articles: {len(self.data)}")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def populate_tree(self):
        """Populate the treeview with data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add data
        for item in self.data:
            self.tree.insert('', tk.END, values=(
                item.get('ID', ''),
                item.get('First_Author', ''),
                item.get('Year', ''),
                item.get('Title', '')[:50] + '...' if len(item.get('Title', '')) > 50 else item.get('Title', ''),
                item.get('Journal', ''),
                item.get('Study_Type', ''),
                item.get('Research_Focus', ''),
                item.get('Screening_Status', ''),
                ', '.join(item.get('Tags', [])) if isinstance(item.get('Tags', []), list) else item.get('Tags', ''),
                item.get('Notes', ''),
                item.get('PDF', ''),
                ', '.join(str(i) for i in item.get('Linked_IDs', [])) if isinstance(item.get('Linked_IDs', []), list) else item.get('Linked_IDs', ''),
                item.get('Audit_Trail', '')
            ))
    def deduplicate_references(self):
        """Deduplicate references by Title and First_Author"""
        seen = set()
        unique = []
        for item in self.data:
            key = (item.get('Title', '').strip().lower(), item.get('First_Author', '').strip().lower())
            if key not in seen:
                seen.add(key)
                unique.append(item)
        removed = len(self.data) - len(unique)
        self.data = unique
        self.populate_tree()
        messagebox.showinfo("Deduplication", f"Removed {removed} duplicates.")

    def export_prisma(self):
        """Export PRISMA flow summary as text file"""
        total = len(self.data)
        included = sum(1 for d in self.data if d.get('Screening_Status') == 'Included')
        excluded = sum(1 for d in self.data if d.get('Screening_Status') == 'Excluded')
        needs_review = sum(1 for d in self.data if d.get('Screening_Status') == 'Needs Review')
        prisma_text = f"PRISMA Flow Summary\nTotal: {total}\nIncluded: {included}\nExcluded: {excluded}\nNeeds Review: {needs_review}"
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")], title="Save PRISMA summary")
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(prisma_text)
            messagebox.showinfo("PRISMA Export", f"PRISMA summary saved to {filename}")

    def bulk_screening(self):
        """Bulk update screening status for selected articles"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Select articles to bulk screen.")
            return
        status = tk.simpledialog.askstring("Bulk Screening", "Enter screening status (Included, Excluded, Needs Review):")
        if status not in ['Included', 'Excluded', 'Needs Review']:
            messagebox.showerror("Invalid", "Status must be Included, Excluded, or Needs Review.")
            return
        for sel in selected:
            item_id = self.tree.item(sel)['values'][0]
            for item in self.data:
                if item['ID'] == item_id:
                    item['Screening_Status'] = status
                    self.add_audit(item, f"Bulk screening set to {status}")
        self.populate_tree()

    def attach_pdf(self):
        """Attach a PDF to the selected article"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Select an article to attach PDF.")
            return
        file = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")], title="Select PDF file")
        if not file:
            return
        item_id = self.tree.item(selected[0])['values'][0]
        for item in self.data:
            if item['ID'] == item_id:
                item['PDF'] = file
                self.add_audit(item, f"PDF attached: {os.path.basename(file)}")
        self.populate_tree()

    def advanced_filter_dialog(self):
        """Open a dialog for advanced filtering"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Advanced Filter")
        dialog.geometry("400x300")
        tk.Label(dialog, text="Field:").pack()
        field_var = tk.StringVar()
        field_entry = ttk.Combobox(dialog, textvariable=field_var, values=list(self.data[0].keys()) if self.data else [])
        field_entry.pack()
        tk.Label(dialog, text="Value contains:").pack()
        value_var = tk.StringVar()
        value_entry = ttk.Entry(dialog, textvariable=value_var)
        value_entry.pack()
        def do_filter():
            field = field_var.get()
            value = value_var.get().lower()
            filtered = [item for item in self.data if value in str(item.get(field, '')).lower()]
            self.data = filtered
            self.populate_tree()
            dialog.destroy()
        ttk.Button(dialog, text="Apply Filter", command=do_filter).pack(pady=10)

    def tag_selected(self):
        """Add tags to selected articles"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Select articles to tag.")
            return
        tag = tk.simpledialog.askstring("Tag", "Enter tag (comma separated for multiple):")
        if not tag:
            return
        tags = [t.strip() for t in tag.split(',')]
        for sel in selected:
            item_id = self.tree.item(sel)['values'][0]
            for item in self.data:
                if item['ID'] == item_id:
                    if 'Tags' not in item or not isinstance(item['Tags'], list):
                        item['Tags'] = []
                    item['Tags'].extend(tags)
                    item['Tags'] = list(set(item['Tags']))
                    self.add_audit(item, f"Tags added: {', '.join(tags)}")
        self.populate_tree()

    def add_note_selected(self):
        """Add a note to selected article"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Select an article to add note.")
            return
        note = tk.simpledialog.askstring("Note", "Enter note:")
        if not note:
            return
        item_id = self.tree.item(selected[0])['values'][0]
        for item in self.data:
            if item['ID'] == item_id:
                item['Notes'] = note
                self.add_audit(item, f"Note added: {note}")
        self.populate_tree()

    def export_subset(self):
        """Export only Included or Needs Review articles"""
        subset = [item for item in self.data if item.get('Screening_Status') in ['Included', 'Needs Review']]
        if not subset:
            messagebox.showwarning("No Data", "No Included or Needs Review articles to export.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], title="Export Subset")
        if filename:
            df = pd.DataFrame(subset)
            df.to_excel(filename, index=False)
            messagebox.showinfo("Export Subset", f"Exported {len(subset)} articles to {filename}")

    def link_references(self):
        """Link selected articles together"""
        selected = self.tree.selection()
        if len(selected) < 2:
            messagebox.showwarning("Selection Required", "Select at least two articles to link.")
            return
        ids = [self.tree.item(sel)['values'][0] for sel in selected]
        for item in self.data:
            if item['ID'] in ids:
                if 'Linked_IDs' not in item or not isinstance(item['Linked_IDs'], list):
                    item['Linked_IDs'] = []
                item['Linked_IDs'] = list(set(item['Linked_IDs'] + [i for i in ids if i != item['ID']]))
                self.add_audit(item, f"Linked to IDs: {', '.join(str(i) for i in ids if i != item['ID'])}")
        self.populate_tree()

    def add_audit(self, item, action):
        """Add an audit trail entry to an item"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        if 'Audit_Trail' not in item or not item['Audit_Trail']:
            item['Audit_Trail'] = ''
        item['Audit_Trail'] += f"[{now}] {action}\n"
    def import_references(self):
        """Import references from RIS, BibTeX, or CSV files"""
        filename = filedialog.askopenfilename(
            filetypes=[("RIS files", "*.ris"), ("BibTeX files", "*.bib"), ("CSV files", "*.csv"), ("All files", "*.*")],
            title="Import references file"
        )
        if not filename:
            return
        try:
            if filename.endswith('.ris'):
                refs = self.parse_ris(filename)
            elif filename.endswith('.bib'):
                refs = self.parse_bibtex(filename)
            elif filename.endswith('.csv'):
                df = pd.read_csv(filename)
                refs = df.to_dict('records')
            else:
                messagebox.showerror("Error", "Unsupported file format")
                return
            # Assign new IDs and add Screening_Status
            max_id = max([item['ID'] for item in self.data], default=0)
            for i, ref in enumerate(refs):
                ref['ID'] = max_id + i + 1
                ref['Screening_Status'] = ''
                ref['Date_Extracted'] = datetime.now().strftime('%Y-%m-%d')
                # Map common fields if missing
                if 'First_Author' not in ref:
                    ref['First_Author'] = ref.get('author', ref.get('AU', ''))
                if 'Title' not in ref:
                    ref['Title'] = ref.get('title', ref.get('TI', ''))
                if 'Journal' not in ref:
                    ref['Journal'] = ref.get('journal', ref.get('JO', ''))
                if 'Year' not in ref:
                    ref['Year'] = ref.get('year', ref.get('PY', ''))
            self.data.extend(refs)
            self.populate_tree()
            messagebox.showinfo("Success", f"Imported {len(refs)} references from {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import references: {str(e)}")

    def parse_ris(self, filename):
        """Parse a RIS file and return a list of dicts"""
        refs = []
        with open(filename, encoding='utf-8') as f:
            entry = {}
            for line in f:
                if line.strip() == '':
                    continue
                if line.startswith('ER  -'):
                    refs.append(entry)
                    entry = {}
                    continue
                m = re.match(r'([A-Z0-9][A-Z0-9])  - (.*)', line)
                if m:
                    tag, value = m.groups()
                    if tag in entry:
                        if isinstance(entry[tag], list):
                            entry[tag].append(value)
                        else:
                            entry[tag] = [entry[tag], value]
                    else:
                        entry[tag] = value
        return refs

    def parse_bibtex(self, filename):
        """Parse a BibTeX file and return a list of dicts (basic)"""
        refs = []
        with open(filename, encoding='utf-8') as f:
            content = f.read()
        entries = re.split(r'@\w+\{', content)[1:]
        for entry in entries:
            fields = {}
            for m in re.finditer(r'(\w+)\s*=\s*[{\"]([^\}\"]+)[}\"]', entry):
                fields[m.group(1).lower()] = m.group(2)
            refs.append(fields)
        return refs
            
        self.status_var.set(f"Total Articles: {len(self.data)}")
        
    def filter_data(self, *args):
        """Filter data based on search term"""
        search_term = self.search_var.get().lower()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Filter and add data
        filtered_count = 0
        for item in self.data:
            if (search_term in item['First_Author'].lower() or 
                search_term in item['Title'].lower() or 
                search_term in item['Journal'].lower() or
                search_term in str(item['Year']).lower()):
                
                self.tree.insert('', tk.END, values=(
                    item['ID'],
                    item['First_Author'],
                    item['Year'],
                    item['Title'][:50] + '...' if len(item['Title']) > 50 else item['Title'],
                    item['Journal'],
                    item['Study_Type'],
                    item['Research_Focus']
                ))
                filtered_count += 1
                
        self.status_var.set(f"Showing {filtered_count} of {len(self.data)} articles")
        
    def add_new_article(self):
        """Open dialog to add new article"""
        self.open_article_dialog()
        
    def edit_selected(self):
        """Edit the selected article"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Required", "Please select an article to edit.")
            return
            
        # Get the ID from the selected item
        item_values = self.tree.item(selected_item[0])['values']
        article_id = item_values[0]
        
        # Find the article in data
        article = next((item for item in self.data if item['ID'] == article_id), None)
        if article:
            self.open_article_dialog(article)
            
    def delete_selected(self):
        """Delete the selected article"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Required", "Please select an article to delete.")
            return
            
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this article?"):
            item_values = self.tree.item(selected_item[0])['values']
            article_id = item_values[0]
            
            # Remove from data
            self.data = [item for item in self.data if item['ID'] != article_id]
            
            # Refresh tree
            self.populate_tree()
            
    def open_article_dialog(self, article=None):
        """Open dialog for adding/editing article"""
        dialog = ArticleDialog(self.root, article)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            if article:  # Editing existing
                # Update existing article
                for i, item in enumerate(self.data):
                    if item['ID'] == article['ID']:
                        self.data[i] = dialog.result
                        break
            else:  # Adding new
                # Assign new ID
                max_id = max([item['ID'] for item in self.data], default=0)
                dialog.result['ID'] = max_id + 1
                dialog.result['Date_Extracted'] = datetime.now().strftime('%Y-%m-%d')
                self.data.append(dialog.result)
                
            self.populate_tree()
            
    def save_to_excel(self):
        """Save data to Excel file"""
        if not self.data:
            messagebox.showwarning("No Data", "No data to save.")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Save as Excel file"
        )
        
        if filename:
            try:
                df = pd.DataFrame(self.data)
                df.to_excel(filename, index=False, sheet_name='Microplastics_Data')
                messagebox.showinfo("Success", f"Data saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                
    def save_to_csv(self):
        """Save data to CSV file"""
        if not self.data:
            messagebox.showwarning("No Data", "No data to save.")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save as CSV file"
        )
        
        if filename:
            try:
                df = pd.DataFrame(self.data)
                df.to_csv(filename, index=False)
                messagebox.showinfo("Success", f"Data saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
                
    def load_from_file(self):
        """Load data from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")],
            title="Load data file"
        )
        
        if filename:
            try:
                if filename.endswith('.xlsx'):
                    df = pd.read_excel(filename)
                elif filename.endswith('.csv'):
                    df = pd.read_csv(filename)
                else:
                    messagebox.showerror("Error", "Unsupported file format")
                    return
                    
                self.data = df.to_dict('records')
                self.populate_tree()
                messagebox.showinfo("Success", f"Data loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")


class ArticleDialog:
    def __init__(self, parent, article=None):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add/Edit Article" if not article else "Edit Article")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Create form
        self.create_form(article)
        
    def create_form(self, article):
        """Create the article form"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Basic Information
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Basic Information")
        
        # Tab 2: Study Details
        study_frame = ttk.Frame(notebook)
        notebook.add(study_frame, text="Study Details")
        
        # Tab 3: Microplastics Info
        mp_frame = ttk.Frame(notebook)
        notebook.add(mp_frame, text="Microplastics")
        
        # Tab 4: Health & Toxicity
        health_frame = ttk.Frame(notebook)
        notebook.add(health_frame, text="Health & Toxicity")
        
        # Tab 5: Additional Info
        additional_frame = ttk.Frame(notebook)
        notebook.add(additional_frame, text="Additional")
        
        # Store entry widgets
        self.entries = {}
        
        # Basic Information fields
        basic_fields = [
            ('First_Author', 'First Author', 'text'),
            ('Year', 'Year', 'text'),
            ('Title', 'Title', 'text'),
            ('Journal', 'Journal', 'text'),
            ('Full_Citation', 'Full Citation', 'text'),
            ('Screening_Status', 'Screening Status', 'combo', ['', 'Included', 'Excluded', 'Needs Review'])
        ]
        self.create_tab_fields(basic_frame, basic_fields)
        
        # Study Details fields
        study_fields = [
            ('Study_Type', 'Study Type', 'combo', ['', 'Experimental', 'Observational', 'Systematic Review', 
                                                   'Meta-analysis', 'Systematic Review & Meta-analysis', 
                                                   'Cross-sectional', 'Cohort', 'Case-control', 'In vitro', 'In vivo']),
            ('Research_Focus', 'Research Focus', 'combo', ['', 'Human Health', 'Reproductive Health', 'Toxicity', 
                                                          'Environmental Distribution', 'Detection Methods', 
                                                          'Ecological Effects', 'Remediation', 'Sources']),
            ('Environment', 'Environment', 'combo', ['', 'Aquatic', 'Terrestrial', 'Marine', 'Freshwater', 
                                                     'Soil', 'Air', 'Food', 'Laboratory']),
            ('Organisms', 'Organisms/Subjects', 'text'),
            ('Sample_Size', 'Sample Size', 'text'),
            ('Geographic_Location', 'Geographic Location', 'text')
        ]
        
        self.create_tab_fields(study_frame, study_fields)
        
        # Microplastics Info fields
        mp_fields = [
            ('MP_Detection_Method', 'Detection Method', 'text'),
            ('MP_Concentration', 'MP Concentration', 'text'),
            ('MP_Size_Range', 'Size Range', 'text'),
            ('MP_Type', 'MP Type/Polymer', 'text'),
            ('Exposure_Route', 'Exposure Route', 'combo', ['', 'Ingestion', 'Inhalation', 'Dermal', 'Multiple']),
            ('Exposure_Duration', 'Exposure Duration', 'text')
        ]
        
        self.create_tab_fields(mp_frame, mp_fields)
        
        # Health & Toxicity fields
        health_fields = [
            ('Health_Effects', 'Health Effects', 'text'),
            ('Toxicity_Endpoints', 'Toxicity Endpoints', 'text'),
            ('Quality_Score', 'Quality Score', 'combo', ['', 'High', 'Moderate', 'Low']),
            ('Risk_of_Bias', 'Risk of Bias', 'combo', ['', 'Low', 'Moderate', 'High', 'Unclear'])
        ]
        
        self.create_tab_fields(health_frame, health_fields)
        
        # Additional Info fields
        additional_fields = [
            ('Key_Findings', 'Key Findings', 'text'),
            ('Study_Limitations', 'Study Limitations', 'text'),
            ('Notes', 'Additional Notes', 'text')
        ]
        
        self.create_tab_fields(additional_frame, additional_fields)
        
        # Fill form if editing
        if article:
            for field, entry in self.entries.items():
                if field in article:
                    if isinstance(entry, ttk.Combobox):
                        entry.set(article[field])
                    else:
                        entry.insert(0, str(article[field]) if article[field] else '')
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Save", command=self.save_article).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT)
        
    def create_tab_fields(self, parent, fields):
        """Create fields for a tab"""
        parent_frame = ttk.Frame(parent)
        parent_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrollable frame
        canvas = tk.Canvas(parent_frame)
        scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for i, field_info in enumerate(fields):
            field_key = field_info[0]
            field_label = field_info[1]
            field_type = field_info[2]
            
            # Label
            ttk.Label(scrollable_frame, text=field_label + ":").grid(
                row=i, column=0, sticky=tk.W, pady=5, padx=(0, 10)
            )
            
            # Entry widget
            if field_type == 'combo':
                values = field_info[3] if len(field_info) > 3 else []
                widget = ttk.Combobox(scrollable_frame, values=values, width=50)
            else:
                widget = ttk.Entry(scrollable_frame, width=50)
                
            widget.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=5)
            scrollable_frame.columnconfigure(1, weight=1)
            
            self.entries[field_key] = widget
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def save_article(self):
        """Save the article data"""
        # Collect data from form
        data = {}
        for field, entry in self.entries.items():
            if isinstance(entry, ttk.Combobox):
                data[field] = entry.get()
            else:
                data[field] = entry.get()
                
        # Basic validation
        if not data.get('First_Author') or not data.get('Title'):
            messagebox.showerror("Validation Error", "Author and Title are required fields.")
            return
            
        # Convert year to int if provided
        if data.get('Year'):
            try:
                data['Year'] = int(data['Year'])
            except ValueError:
                data['Year'] = ''
                
        self.result = data
        self.dialog.destroy()
        
    def cancel(self):
        """Cancel the dialog"""
        self.dialog.destroy()


def main():
    """Main function to run the application"""
    root = tk.Tk()
    
    # Set style
    style = ttk.Style()
    style.theme_use('clam')
    
    app = MicroplasticsDataExtractor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
