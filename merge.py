#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3, sys, zipfile, os, gzip, re
import cStringIO

con_cn=sqlite3.connect('basewords.db')
con_en=sqlite3.connect('dictionary.db')

cur_cn=con_cn.cursor()
cur_en=con_en.cursor()
cur_out=con_en.cursor()

def clear_desc(desc):
    desc = desc.replace(u"\ufeff", "")
    desc = desc.replace(u"\r\n", "\n")
    return desc

def extract_zip(blobbuf):
    input_zip=zipfile.ZipFile(cStringIO.StringIO(blobbuf), 'r')
    return {name: clear_desc(unicode(input_zip.read(name),'utf-8')) for name in input_zip.namelist()}

def get_cn_desc(blobbuf):
    return extract_zip(blobbuf).values()[0]

def find_cn(word):
    cur_cn.execute("select term, description from tblWords where term = ? ", (word,))
    result = cur_cn.fetchone() 
    return (result[0], get_cn_desc(result[1]))

def all_cn_words():
    cur_cn.execute('select term,description from tblWords')
    while True:
        result = cur_cn.fetchmany(100)
        if not result:
            break
        for r in result:
            yield r

def extract_gzip(blobbuf):
    input_gzip=gzip.GzipFile(fileobj=cStringIO.StringIO(blobbuf), mode='r')
    return unicode(input_gzip.read(), 'utf-8')

def find_en(word):
    cur_en.execute("select _id, description from tblWords where term = ? ", (word,))
    result =cur_en.fetchone()
    return (result[0], extract_gzip(result[1]))

def compress(desc):
    stringio = cStringIO.StringIO()
    gzip_file = gzip.GzipFile(fileobj=stringio, mode='w')
    gzip_file.write(desc)
    gzip_file.close()
    return stringio.getvalue()

def insert_word(term, desc):
    gzip_desc = compress(desc.encode('utf-8'))
    cur_out.execute("INSERT INTO tblWords (term, description) VALUES (?, ?)", ( term, sqlite3.Binary(gzip_desc)))

def update_word(id, term, desc):
    gzip_desc = compress(desc.encode('utf-8'))
    cur_out.execute("UPDATE tblWords set description = ? where _id = ?)", ( sqlite3.Binary(gzip_desc), _id))

body_with_entry=re.compile(u"<body>\n<div>\n<div class=\"entry\">(.*)</div>\n</div>\n</body>", re.MULTILINE | re.DOTALL)
body=re.compile(u"<body>(.*)</body>", re.MULTILINE | re.DOTALL)

def extract_desc (desc):
    m = body_with_entry.search(desc)
    if m is not None:
        return m.group(1)
    m = body.search(desc)
    if m is not None:
        return m.group(1)
    return desc

def create_div_entry(desc):
    content = extract_desc(desc)
    return u"""<div class="entry">
%s
</div>""" % (content,)


for word in all_cn_words():
      term = word[0]
      description = create_div_entry(get_cn_desc(word[1]))
      #print term, description
      insert_word(term, description)

con_en.commit()
