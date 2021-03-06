#!/usr/bin/python

# Bandcamp Mp3 Downloader
# Copyright (c) 2012 cisoun, Cyriaque Skrapits <cysoun[at]gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributors:
#	JamieMellway
#	jtripper


VERSION = "0.1.12 DIFEGUEMOD Augmented Edition"

import os

import sys
import urllib.request
import re
import json
import math

from datetime import datetime, date, time
try:
	import stagger
	from stagger.id3 import *
	can_tag = True
except:
	print("[Error] Can't import stagger, will skip mp3 tagging.")
	can_tag = False
	
try:
	import pyperclip
	can_paper = True
except:
	print("[Error] Can't import pyperclip, paperclip features unavailable.")
	can_paper = False

# Download a file and show its progress.
# Taken from http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
def Download(url, out, message):
	# Check if the file is availabe otherwise, skip.
	if not re.match("^https?://(\w+)\.(\w+)\.([\w\?\/\=\-\&\.])*$", str(url)):
		return(False)
	# Let's do this !
	print("Downloading to "+out)
	u = urllib.request.urlopen(url)
	f = open(out, "wb")
	meta = u.info()
	file_size = int(meta["Content-Length"])
	file_size_dl = 0
	block_sz = 8192
	t = message 
	pb_len = 25
	space_len = 80 - pb_len - len(t) - 2
	while True:
		buffer = u.read(block_sz)
		if not buffer:
			break
		file_size_dl += len(buffer)
		f.write(buffer)
		progress = math.ceil(file_size_dl * pb_len / file_size)
		t2 = t + " (" + str(int(file_size_dl / 1024)) +"/"+ str(int(file_size / 1024)) + " ko) : " 
		status = t2 + "[" + ("#" * progress) + (" " * (pb_len - progress)) + "]"
		status = status + chr(8) * (len(status))
		sys.stdout.write(status)
		sys.stdout.flush()
	f.close()
	print()
	return(True)

# Return some JSON things...
def GetDataFromProperty(p, s, bracket = False):
	try:
		if bracket:
			return(json.loads("[{" + (re.findall(p + "[ ]?: \[?\{(.+)\}\]?,", s, re.MULTILINE)[0] + "}]")))
		return(re.findall(p + "[ ]?: ([^,]+)", s, re.DOTALL)[0])
	except:
		return(0)

# Print a JSON data.
def PrintData(d):
	print(json.dumps(d, sort_keys = True, indent = 2))

def getTitleFilename(title):
	allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789-_()"
	return ''.join(c for c in title if c in allowed)
	

#===============================================================================
#
#	MAIN CODE
#
#===============================================================================
def bcDL(url):

	# Load the code.
	try:
		f = urllib.request.urlopen(url)
		s = f.read().decode('utf-8')
		f.close()
	except:
		print("[Error] Can't reach the page.")
		print("Aborting...")
		sys.exit(0)

	# We only load the essential datas.
	tracks = GetDataFromProperty("trackinfo", s, True)
	if tracks == 0 :
		print("[Error] Tracks not found. This is necessary to continue.")
		print("Aborting...")
		sys.exit(0)
	album = GetDataFromProperty("current", s, True)[0]
	artist = GetDataFromProperty("artist", s).replace('"', '').replace('\\', '')
	artwork = GetDataFromProperty("artThumbURL", s).replace('"', '').replace('\\', '')
	artwork_full = GetDataFromProperty("artFullsizeUrl", s).replace('"', '').replace('\\', '')
	if album == 0 : print("[Warning] Album informations not found.")
	if artist == 0 : print("[Warning] Artist informations not found.")
	if artwork == 0  : print("[Warning] Cover not found.")
	if artwork_full == 0  : print("[Warning] Full size cover not found.")
	try:
		release_date = datetime.strptime(album["release_date"], "%d %b %Y %H:%M:%S GMT")
	except:
		print("[Warning] Cannot find release date.")


#===============================================================================
#
#	3. Download & tag.
#
#===============================================================================
	#Create dir for Album.
	pathd = os.getcwd()+"\\"+getTitleFilename(artist+" - "+album["title"])+"\\"
	if not os.path.exists(pathd):
		os.makedirs(pathd)
	os.chdir(pathd)
	
	# List the tracks.
	print("\nTracks found :\n----")
	for i in range(0, len(tracks)):
		# Track number available ?
		track_num = str(tracks[i]["track_num"]) + ". " if tracks[i]["track_num"] != None else ""
		print(track_num + str(tracks[i]["title"]))
	exit
	# Artwork.
	print()
	artwork_name = artwork.split('/')[-1]
	artwork_full_name = artwork_full.split('/')[-1]
	Download(artwork, artwork_name, "Cover")
	Download(artwork_full, artwork_full_name, "Fullsize cover")

	# Tracks.
	print()
	got_error = False
	for track in tracks:
		# Skip track number if missing.
		if track["track_num"] != None:
			f = "%02d. %s.mp3" % (track["track_num"], track["title"].replace("\\", "").replace("/", ""))
		else:
			f = "%s.mp3" % track["title"].replace("\\", "").replace("/", "")
		# Skip if file unavailable. Can happens with some albums.
		message = "Track " + str(tracks.index(track) + 1) + "/" + str(len(tracks))
		try:
			downloaded = Download(track["file"]["mp3-128"], f, message)
			if not downloaded:
				raise Exception
		except Exception:
			got_error = True
			print(message + " : File unavailable. Skipping...")
			continue

		# Tag.
		if can_tag == False : continue # Skip the tagging operation if stagger cannot be loaded.
		# Try to load the mp3 in stagger.
		print("Tagging "+f)
		try:
			t = stagger.read_tag(f)
		except:
			# Try to add an empty ID3 header.
			# As long stagger crashes when there's no header, use this hack.
			# ID3v2 infos : http://id3.org/id3v2-00
			m = open(f, 'r+b')
			old = m.read()
			m.seek(0)
			m.write(b"\x49\x44\x33\x02\x00\x00\x00\x00\x00\x00" + old) # Meh...
			m.close
		# Let's try again...
		try:
			t = stagger.read_tag(f)
			t.album = album["title"]
			t.artist = artist
			if release_date.strftime("%H:%M:%S") == "00:00:00":
				t.date = release_date.strftime("%Y-%m-%d")
			else:
				t.date = release_date.strftime("%Y-%m-%d %H:%M:%S")
			t.title = track["title"]
			t.track = track["track_num"]
			t.picture = artwork_full_name
			t.write()
		except:
			print("[Warning] Can't add tags, skipped.")
	if got_error:
		print()
		print(80 * "=")
		print("OOPS !")
		print("Looks like some tracks haven't been reached.")
		print("It can happen with some albums. They sometimes don't allow to listen to some of their tracks. Sorry for you.")
		print(80 * "=")


#===============================================================================
#
#	4. Add album's informations.
#
#===============================================================================

	
	print("\nAdding additional infos...")
	f = open("INFOS.txt", "w+")
	f.write("Artist : " + artist)
	if album["title"] != None : f.write("\nAlbum : " + album["title"])
	if release_date != None : f.write("\nRelease date : " + release_date.strftime("%Y-%m-%d %H:%M:%S"))
	if album["credits"] != None : f.write("\n\nCredits :\n----\n" + album["credits"])
	if album["about"] != None : f.write("\n\nAbout :\n----\n" + album["about"])
	f.close()

	# Done.
	print("\nFinished !\n")
