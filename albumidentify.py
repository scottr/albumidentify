#!/usr/bin/python2.5
import sys
import fingerprint
import musicdns
import os
import flacnamer

key = 'a7f6063296c0f1c9b75c7f511861b89b'

def decode(frommp3name, towavname):
	print "Decoding %(frommp3name)s" % locals()
	os.system("mpg123 --quiet --wav \"%(towavname)s\" \"%(frommp3name)s\"" % locals())


def get_dir_info(dirname):
	files=os.listdir(dirname)
	files.sort()
	tracknum=0
	trackinfo={}
	for i in files:
		tracknum=tracknum+1
		if not i.endswith(".mp3"):
			print "Skipping non mp3 file",`i`
			continue
		fname=os.path.join(dirname,i)
		# While testing this uses a fixed name in /tmp
		# and checks if it exists, and doesn't decode if it does.
		# This is for speed while debugging, should be changed with
		# tmpname later
		toname=os.path.join("/tmp/",i[:-3]+"wav")
		if not os.path.exists(toname):
			decode(fname,toname)
		(fp, dur) = fingerprint.fingerprint(toname)

		(trackname, artist, puid) = musicdns.lookup_fingerprint(fp, dur, key)
		tracks = flacnamer.get_tracks_by_puid(puid)
		trackinfo[tracknum]=(fname,artist,trackname,dur,tracks)
	return trackinfo

def guess_album(trackinfo):
	# tracinfo is
	#  <tracknum> => (fname,artist,trackname,dur,[mbtrackids])
	#
	# returns a list of possible release id's
	possible_releases={}
	for (tracknum,(fname,artist,trackname,dur,tracks)) in trackinfo.items():
		for track in tracks:
			for r in track.getReleases():
				if tracknum>1 and (
					r.id not in possible_releases 
					or possible_releases[r.id] != tracknum-1):
					# Skip this album -- we know it's not going to
					# be a final candidate
					continue
				# Get the information about this release
				release = flacnamer.get_release_by_releaseid(r.id)
				# Skip if this album has the wrong number of tracks.
				if len(release.getTracks()) != len(trackinfo):
					continue
				# Skip if the tracks in the wrong place on this album
				if flacnamer.track_number(release.getTracks(), track.title) != tracknum:
					continue
				if release.id in possible_releases:
					possible_releases[release.id] += 1
				else:
					possible_releases[release.id] = 1
	releasedata=[]

	for rid in [x for x in possible_releases if possible_releases[x]==len(trackinfo)]:
		release = flacnamer.get_release_by_releaseid(rid)
		albumartist=release.getArtist()
		#print albumartist.name,":",release.title+" ("+rid+")"
		releaseevents=release.getReleaseEvents()
		#print "Release dates:"
		#for ev in releaseevents:
		#	print " ",ev.date
		#print "Track:"
		tracks=release.getTracks()
		trackdata=[]
		for tracknum in range(len(tracks)):
			trk=tracks[tracknum]
			(fname,artist,trackname,dur,trackprints) = trackinfo[tracknum+1]
			if trk.artist is None:
				artist=albumartist.name
			else:
				artist=trk.artist.name
			#print " ",tracknum+1,"-",artist,"-",trk.title,"%2d:%06.3f" % (int(dur/60000),(dur%6000)/1000),`fname`
			trackdata.append((tracknum+1,artist,trk.title,dur,fname))
		albuminfo = (
			albumartist.name,
			release.title,
			rid+".html",
			[x.date for x in releaseevents],
			trackdata
		)
		releasedata.append(albuminfo)
	return releasedata

if __name__=="__main__":
	trackinfo=get_dir_info(sys.argv[1])
	print guess_album(trackinfo)
	#return releasedata
