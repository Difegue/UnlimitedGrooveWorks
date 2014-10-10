#!/usr/bin/python

import sys
import re
import pyperclip
import bandcamp
import soundclouDL


if __name__ == "__main__":

	print("=" * 80)
	print("\tI am the bone of my music")
	print("\tBass is my body and treble is my blood")
	print("\tI have ripped over a thousand mp3s,")
	print("\tUnknown to 320kpbs, Nor known to FLAC")
	print("\tHave withstood pain to download many songs")
	print("\tYet, those hands will never buy anything")
	print("\tSo as I pray, unlimited groove works. \n")
	print("=" * 80)
	print()

	if len(sys.argv) == 1:
		print("No URL detected at the end of the command.")
		print("e.g: " + sys.argv[0] + " http://artist.bandcamp.com/album/blahblahblah\n")
		
		if pyperclip.paste() != "":
			if input("Text detected in paperclip. Use " + str(pyperclip.paste())[2:-1] + "?[y/n] : ") != "y": 
				url=input("Input url now, and press ENTER. \n")
			else: url = str(pyperclip.paste())[2:-1]
	else:
	    url = sys.argv[1]
		
	print("URL selected: " + url)
	
	if re.match("^https?://soundcloud\.com([-\w]|/)*$", url):
		print("Soundcloud URL detected.")
		soundclouDL.scDL(url)
	else:
		print("Not a soundcloud URL. Treating as bandcamp...")
		bandcamp.bcDL(url)
		