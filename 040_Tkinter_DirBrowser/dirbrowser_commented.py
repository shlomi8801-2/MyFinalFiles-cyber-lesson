#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A simple directory browser GUI using Tkinter's themed widgets (ttk).
The UI consists of a Treeview showing the current directory contents and
two scrollbars that auto-hide when not needed.

This script demonstrates:
- How to populate a Treeview lazily (only when a directory node is expanded)
- How to attach vertical/horizontal scrollbars that auto-hide
- How to react to UI events (double-click, open-node) to navigate the filesystem
"""

import os                   # File-system path operations and stat info
import glob                 # For expanding patterns like '.' and '..' in a cross-platform way
import tkinter              # Core Tkinter module for GUI
from tkinter import ttk     # Themed widgets: Treeview, Scrollbar, etc.

# Emoji fallback if PNGs are missing/unreadable
EMOJI_PREFIX = {
    'directory': '📁 ',
    'file': '📄 ',
}

ICON_FILES = {
    'directory': 'folder.png',
    'file': 'file.png',
}

# ---------- Helpers ----------


def format_size(num_bytes: int) -> str:
    """Convert size in bytes to a human-readable string."""
    try:
        n = float(num_bytes)
    except Exception:
        return "—"

    units = ["bytes", "KB", "MB", "GB", "TB"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024.0
        i += 1
    if i == 0:
        return f"{int(n)} {units[i]}"
    return f"{n:.1f} {units[i]}"


def try_load_icons(_root: tkinter.Tk) -> dict:
    """
    Attempt to load PNG icons from files located next to this script.
    Returns a dict with keys 'directory' and 'file' mapping to tkinter.PhotoImage,
    or None values if loading failed (caller should handle fallback text).
    """
    images = {'directory': None, 'file': None}
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # __file__ may not exist in some embedded scenarios; use CWD
        base_dir = os.getcwd()

    for key, fname in ICON_FILES.items():
        path = os.path.join(base_dir, fname)
        if os.path.isfile(path):
            try:
                images[key] = tkinter.PhotoImage( file=path, master=_root )
            except Exception:
                images[key] = None
        else:
            images[key] = None
    return images

# ---------- Tree population ----------


def populate_tree(tree: ttk.Treeview, node: str, images: dict) -> None:
    """
    Expand a given Treeview 'node' by listing its directory entries.

    The Treeview stores metadata in hidden columns:
    - 'fullpath' contains the absolute path represented by each node
    - 'type' is either 'directory' or 'file'
    - 'size' is a human-readable string (only for files)

    We only proceed if the node represents a directory. For files,
    there is nothing to expand.

    Parameters
    ----------
    tree : ttk.Treeview
        The widget that holds the directory structure.
    node : str
        The item ID (iid) of the node to populate.
    images: dict
        Icons
    """
    if tree.set(node,"type") != 'directory':
        return

    path = tree.set(node,"fullpath")
    tree.delete(*tree.get_children(node))

    parent = tree.parent(node)
    special_dirs = [] if parent else (glob.glob('.') + glob.glob('..'))

    try:
        listing = special_dirs + os.listdir(path)
    except Exception:
        listing = special_dirs

    for entry in listing:
        p = os.path.join(path,entry).replace('\\','/')
        if os.path.isdir(p):
            ptype = "directory"
        elif os.path.isfile(p):
            ptype = "file"
        else:
            continue

        fname = os.path.split(p)[1]
        text = (EMOJI_PREFIX[ptype] if images[ptype] is None else '') + fname

        item_id = tree.insert(
            node,"end",
            text=text,
            values=[p,ptype,""],  # fullpath, type, size
            image=(images[ptype] if images[ptype] is not None else "")
        )

        if ptype == 'directory':
            if fname not in ('.','..'):
                # Dummy child so arrow appears
                tree.insert(item_id,0,text="dummy",
                            image=(images['file'] if images['file'] is not None else ""))
                tree.item(item_id,text=text)
        else:
            try:
                size = os.stat(p).st_size
            except OSError:
                size = 0
            tree.set(item_id,"size",format_size(size))


def populate_roots(tree: ttk.Treeview, images: dict) -> None:
    """
    Create the root node representing the current working directory,
    then populate its first level of children.

    Parameters
    ----------
    tree : ttk.Treeview
        The widget to receive the root item.
    """
    # Absolute path of the current working directory (normalized with forward slashes)
    cwd = os.path.abspath('.').replace('\\', '/')

    text = (EMOJI_PREFIX['directory'] if images['directory'] is None else '') + cwd

    # Insert a top-level item with the directory's absolute path.
    root_id = tree.insert(
        '','end',
        text=text,
        values=[cwd,"directory",""],
        image=(images['directory'] if images['directory'] is not None else "")
    )

    # Populate the just-created root directory node.
    populate_tree(tree, root_id, images)

# ---------- Event handlers ----------


def on_tree_open(event) -> None:
    """
    Event handler for '<<TreeviewOpen>>' (node expansion). When a node is
    expanded by the user, we populate it with its children. This is the
    essence of 'lazy loading': we only expand when needed.
    """
    tree = event.widget  # The Treeview that triggered the event
    images = tree.images_ref  # stored on widget
    populate_tree(tree, tree.focus(), images)  # Expand the node that's now focused/expanded


def on_tree_double_click(event) -> None:
    """
    Event handler for double-clicks. If the user double-clicks a *directory*
    (that isn't the very top-level), we change the process current working
    directory to that path and rebuild the Treeview to reflect the new context.

    Note:
    - Changing the process CWD is a global state change. In larger apps,
      consider keeping the path as app state instead of calling os.chdir.
    """
    tree = event.widget
    node = tree.focus()  # Item that was double-clicked

    # Only act if the node has a parent (i.e., not the very root Treeview node).
    if tree.parent(node):
        # Absolute path stored in the 'fullpath' hidden column.
        path = os.path.abspath(tree.set(node, "fullpath"))
        if os.path.isdir(path):
            # Change current working directory to the selected one.
            os.chdir(path)

            # Clear out any existing top-level items and rebuild the tree.
            tree.delete(*tree.get_children(''))
            images = tree.images_ref
            populate_roots(tree, images)


def autoscroll(sbar: ttk.Scrollbar, first: str, last: str) -> None:
    """
    Hide the scrollbar if the entire content is visible; otherwise show it.

    Treeview (and other scrollable widgets) call the yscroll/xscroll command
    with two floats in string form ('first', 'last') that represent the
    fraction of the visible area (0.0 - start, 1.0 - end).
    When the entire content is visible (first <= 0 and last >= 1), we hide
    the scrollbar by removing it from the grid. Otherwise, we show it.

    Parameters
    ----------
    sbar : ttk.Scrollbar
        The scrollbar widget to hide/show.
    first : str
        Start of the visible region as a float string.
    last : str
        End of the visible region as a float string.
    """
    # Convert incoming fractions to floats for comparison.
    first_f, last_f = float(first), float(last)

    # If everything is visible, remove the scrollbar from the layout grid.
    if first_f <= 0 and last_f >= 1:
        sbar.grid_remove()
    else:
        # Otherwise make sure it is visible.
        sbar.grid()

    # Update the scrollbar slider to reflect the new view.
    sbar.set(first, last)


# ---------------------------
# GUI construction starts here
# ---------------------------

# Create the main application window (the "root" Tk instance).
root = tkinter.Tk()
root.title("Directory Browser (Tkinter + ttk)")  # Add a nice title to the window

# Try to load icons and keep references to avoid GC
IMAGES = try_load_icons(root)

# Create vertical and horizontal scrollbars.
# We don't set their 'command' yet; it will be hooked up to the tree's view funcs.
vsb = ttk.Scrollbar(orient="vertical")
hsb = ttk.Scrollbar(orient="horizontal")

# Create the Treeview that will display our filesystem tree.
# - 'columns' defines hidden data columns; '#0' is the implicit Treeview text column.
# - 'displaycolumns' controls which of the defined columns are actually visible.
#   Here we only show the 'size' column; 'fullpath' and 'type' are hidden metadata.
tree = ttk.Treeview(
    columns=("fullpath", "type", "size"),
    displaycolumns=("size",),  # show only the size column; keep others hidden
    yscrollcommand=lambda f, l: autoscroll(vsb, f, l),  # hook autoscroll for vertical
    xscrollcommand=lambda f, l: autoscroll(hsb, f, l),  # hook autoscroll for horizontal
)

# Store images dict on the widget to access in callbacks and keep alive
tree.images_ref = IMAGES

# Wire the scrollbars to control the Treeview viewport.
vsb.configure(command=tree.yview)
hsb.configure(command=tree.xview)

# Configure the column headers.
# '#0' is the implicit first column that displays the 'text' of each item.
tree.heading("#0", text="Directory Structure", anchor='w')
tree.heading("size", text="File Size", anchor='w')

# Width and resize behavior for the visible 'size' column.
tree.column("size", stretch=False, width=120)

# Build the initial contents: insert the root directory and its children.
populate_roots(tree, IMAGES)

# Bind events:
# - When a directory is expanded, populate it lazily.
tree.bind('<<TreeviewOpen>>', on_tree_open)
# - Double-click on an item to change into that directory (rebuild tree).
tree.bind('<Double-Button-1>', on_tree_double_click)

# -------------------------
# Layout (grid geometry mgr)
# -------------------------

# Place the widgets in a 2x2 grid:
# [ Treeview ][  VSB ]
# [   HSB    ][      ]
tree.grid(column=0, row=0, sticky='nswe')
vsb.grid(column=1, row=0, sticky='ns')
hsb.grid(column=0, row=1, sticky='ew')

# Make the main cell with the tree expand when the window is resized.
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

# Start the Tk event loop (blocks until the window is closed).
root.mainloop()
