#!/usr/bin/python
# March 8, 2014
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse
import sys
import argparse
import re
import requests
import time
import soundcloud
import math
import os
import stagger

class SoundCloudDownload:
   def __init__(self, url):
      self.url = url
      self.download_progress = 0
      self.current_time = time.time()
      self.titleList = []
      self.pureTitleList = []
      self.artistList = []
      self.likes = False   
      self.streamURLlist = self.getStreamURLlist(self.url)

   def getStreamURLlist(self, url):
      streamList = []
      tracks = []
      if "/likes" in url:
         url = url[:-6]
         self.likes = True
      api = "http://api.soundcloud.com/resolve.json?url={0}&client_id=YOUR_CLIENT_ID".format(url)
      r = requests.get(api)
      try:
         user = r.json()['username']
         username = r.json()['username']
         user = r.json()['id']
         span = math.ceil(r.json()['public_favorites_count']/float(200)) if self.likes else math.ceil(r.json()['track_count']/float(200))

         for x in range(0, int(span)):
            if self.likes:
               api = "http://api.soundcloud.com/users/" + str(user) + "/favorites.json?client_id=fc6924c8838d01597bab5ab42807c4ae&limit=200&offset=" + str(x * 200)
            else:
               api = "http://api.soundcloud.com/users/" + str(user) + "/tracks.json?client_id=fc6924c8838d01597bab5ab42807c4ae&limit=200&offset=" + str(x * 200)
            r = requests.get(api)
            tracks.extend(r.json())
      except:
         try:
            tracks = r.json()['tracks']
            # If this isn't a playlist, just make a list of
            # a single element (the track)
         except:
            tracks = [r.json()]
      if 'username' in locals():
         pathd = os.getcwd()+"\\"+str(username)+"\\"
         if not os.path.exists(pathd):
            os.makedirs(pathd)
         os.chdir(pathd)
      for track in tracks:
         waveform_url = track['waveform_url']
         self.titleList.append(self.getTitleFilename(track['title']))
         self.pureTitleList.append(track['title'])
         self.artistList.append(track['user']['username'])
         regex = re.compile("\/([a-zA-Z0-9]+)_")
         r = regex.search(waveform_url)
         stream_id = r.groups()[0]
         streamList.append("http://media.soundcloud.com/stream/{0}".format(stream_id))
      return streamList

   def addID3(self, title, title2, artist):
        print("Tagging "+"{0}.mp3".format(title))
        try:
            t = stagger.read_tag("{0}.mp3".format(title))
        except:
            # Try to add an empty ID3 header.
            # As long stagger crashes when there's no header, use this hack.
            # ID3v2 infos : http://id3.org/id3v2-00
            m = open("{0}.mp3".format(title), 'r+b')
            old = m.read()
            m.seek(0)
            m.write(b"\x49\x44\x33\x02\x00\x00\x00\x00\x00\x00" + old) # Meh...
            m.close
        # Let's try again...
        try:
            t = stagger.read_tag("{0}.mp3".format(title))
            # Slicing is to get the whole track name
            # because SoundCloud titles usually have
            # a dash between the artist and some name
            split = title2.find("-")
            if not split == -1:
                t.title = title2[(split + 2):] 
                t.artist = title2[:split] 
            else:
                t.title = title2
                t.artist = artist
            t.write()
        except:
            print("[Warning] Can't add tags, skipped.")
   
   def downloadSongs(self):
      done = False
      for artist, title, title2, streamURL in zip(self.artistList, self.titleList, self.pureTitleList, self.streamURLlist):
         if not done:
            filename = "{0}.mp3".format(title)
            
            sys.stdout.write("\nDownloading: {0}\n".format(filename))
            try:
               if not os.path.isfile(filename):
                  filename, headers = urllib.request.urlretrieve(url=streamURL, filename=filename, reporthook=self.report)
                  self.addID3(title, title2, artist)
                  # reset download progress to report multiple track download progress correctly
                  self.download_progress = 0
               elif self.likes:
                  print("File Exists")
                  done = True
               else:
                  print("File Exists")
            except Exception as e:
               print (e)
   
   def report(self, block_no, block_size, file_size):
      self.download_progress += block_size
      rProgress = round(self.download_progress/1024.00/1024.00, 1)
      rFile = round(file_size/1024.00/1024.00, 1)
      progress = round(25 * float(self.download_progress)/float(file_size))
      t2 = " (" + str(rProgress) +"/"+ str(rFile) + " MB) : " 
      status = t2 + "[" + ("#" * progress) + (" " * (25 - progress)) + "]"
      status = status + chr(8) * (len(status))
      sys.stdout.write(status)
      sys.stdout.flush()

        ## Convenience Methods
   def getTitleFilename(self, title):
                '''
                Cleans a title from Soundcloud to be a guaranteed-allowable filename in any filesystem.
                '''
                allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789-_()"
                return ''.join(c for c in title if c in allowed)

def scDL(url):
   download = SoundCloudDownload(url)
   download.downloadSongs()
   print("\nFinished !\n")

