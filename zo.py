#!/usr/bin/env python
import fnmatch 
import sys
import warnings
import argparse
from os import walk, path, getenv, system

def latex_cites(project):
    """Finds the contents of every \cite command in a LaTeX project within
    a directory, searched recursively.

    Parameters:
    ----------
    project : string
        The name of the directory containing the LaTeX project.
    
    Returns:
    -------
    cites : set of strings
        The contents of all cite commands in the project directory.
    """
    tex_files = set()
    for root, dirnames, filenames in walk(project):
        for filename in fnmatch.filter(filenames, '*.tex'):
            if filename[0] != '.':
                tex_files.add(path.join(root, filename))
    
    cites = set()
    for tex_file in tex_files:
       with open(tex_file, 'r') as f:
          lines = "".join(line.strip() for line in f)
          for b in lines.split("\cite{")[1:]:
              for c in b.split("}")[0].split(","):
                  if c:
                      cites.add(c.strip())
                  else:
                      warnings.warn("Empty citation encountered.", Warning)
    return cites

def bib_nicknames(bib):
    """Finds all the nicknames in BibTeX .bib file.

    Parameters:
    -----------
    bib : str
        Name of the .bib file

    Returns:
    --------
    nicknames : set of strings
        All nicknames within the .bib file
    """
    nicknames = set()
    if path.exists(bib):
        with open(bib, 'r') as f:
            for line in f.readlines():
                if line[0] == '@':
                    nicknames.add(line.split('{')[1].split(',')[0].strip())
    return nicknames

def bib_strip(parent_bib, entries):
    """Strips a subset of entries from a BibTeX .bib file
    
    Parameters:
    ----------
    parent_bib : str
        The parent .bib file
    entries : set of strings
        The BibTeX nicknakes of the entries to be stripped out

    Returns:
    --------
    child_bib : str
        The requested entries
    added_entries : set
        The BibTeX nicknames of the files that were successfully added.
    missing_entries : set
        BibTeX nicknames that were not found in parent_bib
    """
    added_entries = set()
    child_bib = ""
    with open(parent_bib, 'r') as f:
        line = f.readline()
        while line != "":
            if line.strip() != "" and line.strip()[0] == '@' \
                and line.split('{')[1].split(',')[0].strip() in entries:
                entry = line.split('{')[1].split(',')[0].strip() 
                entries.remove(entry)
                added_entries.add(entry)
                child_bib += line
                line = f.readline()
                while line.strip() != "" and line.strip()[0] != '@':
                    if line.strip()[0] != '#':
                        child_bib += line
                    line = f.readline()
                child_bib += "\n"
            else:
                line = f.readline()

    missing_entries = entries # all entries not added
    return child_bib, added_entries, missing_entries

def find_pdfs(dir):
    files = set()
    for root, dirnames, filenames in walk(dir):
        for filename in fnmatch.filter(filenames, '*.pdf'):
            files.add(filename.split(".")[0])

    return(files)

def _printer(things, msg):
    out = ""
    if len(things) > 0:
        out += msg + "\n"
        out += "="*len(msg) + "\n"
        for i, thing in enumerate(things):
            out += "{0}. {1}\n".format(i+1, thing)
    return out

def make(project, parent):
    cites = latex_cites(project)
    local_refs = bib_nicknames(project + "/refs.bib")
    required_refs = cites - local_refs
    append_string, added_refs, missing_refs = bib_strip(parent, required_refs)
    
    with open("refs.bib", 'a') as f:
        f.write(append_string)

    out = _printer(added_refs, 
                   "\nThe following refs were added to the local refs.bib:")
    out += _printer(missing_refs, 
                    "\nRefs not in parent and NOT added to the local refs.bib:")
    print(out)

def status():
    files = find_pdfs(path.join(getenv("HOME"), "refs"))
    refs = bib_nicknames(path.join(getenv("HOME"), "refs", "refs.bib"))
    out = _printer(files & refs, "Files that are good to go:")
    out += _printer(files - refs, "\nFiles missing .bib entries:")
    out += _printer(refs - files, "\n.bib entries missing files:")
    print(out)

def grep(args):
    system('find $HOME/refs/ -name "*.pdf" | xargs -I @ pdftotext @ - | grep {0}'. format(" ".join(args)))

def vince(nickname):
    system('evince $HOME/refs/{0}.pdf &>/dev/null &'. format(nickname))


def main():
   if len(sys.argv) < 2 or sys.argv[1] not in ('status', 'make', 'grep', 'vince'):
       raise ValueError("'zo status' and 'zo make' are the only valid commands")
   if sys.argv[1] == 'status':
       status()
   if sys.argv[1] == 'grep':
       grep(sys.argv[2:])
   if sys.argv[1] == 'vince':
       vince(sys.argv[2])
   parent = path.join(getenv("HOME"), "refs", "refs.bib")
   if len(sys.argv) == 4 and sys.argv[2] in ("--parent", "-p"):
       parent = sys.argv[3]
   if sys.argv[1] == 'make':
       make(".", parent)

if __name__ == '__main__':
    main()
