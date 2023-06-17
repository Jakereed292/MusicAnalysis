from music21 import *

def getAllChords(measure, chordList, count):
    
    for chord in measure.recurse().getElementsByClass('Chord'):
        chordList.append(chord)
        
        if len(chord.pitches) >= 3:
            count += 1
            
    return chordList,count

def getHarmonicTrack(trackList):
    trackDict = {"Track": [], "Count": []}
    
    for i in range(len(trackList)):
        count = 0
        chordList = []
        for m in trackList[i].measures(0, None):
            results = getAllChords(m, chordList, count)
            chordList = results[0]
            count = results[1]
            
        trackDict["Track"].append(chordList)
        trackDict["Count"].append(count)
        
    #for x in range(len(trackDict["Track"])):
    #    count = 0
    #    for y in range(len(trackDict["Track"][x])):
    #        if len(trackDict["Track"][x][y].pitches) >= 3:
    #            count += 1
    #            
    #    trackDict["Count"][x] = count
    
    return trackDict["Track"][trackDict["Count"].index(max(trackDict["Count"]))]

def open_midi(midi_path, remove_drums):
    # There is an one-line method to read MIDIs
    # but to remove the drums we need to manipulate some
    # low level MIDI events.
    
    trackList = []
    
    mf = midi.MidiFile()
    mf.open(midi_path)
    mf.read()
    mf.close()
    
    if (remove_drums):
        for i in range(len(mf.tracks)):
            mf.tracks[i].events = [ev for ev in mf.tracks[i].events if ev.channel != 10]          

    for i in range(len(mf.tracks)):
        trackList.append(midi.translate.midiTrackToStream(mf.tracks[i]))

    return getHarmonicTrack(trackList)

def getKey(midi_path):
    mf = midi.MidiFile()
    mf.open(midi_path)
    mf.read()
    mf.close()

    for i in range(len(mf.tracks)):
        mf.tracks[i].events = [ev for ev in mf.tracks[i].events if ev.channel != 10]          

    score = stream.Score()
    midiChords = midi.translate.midiFileToStream(mf).chordify()
    score.insert(0, midiChords)
    
    songKey = score.analyze('key')
    return songKey

def cleanChords(chordListIn):
    list = []
    returnList = []
    
    for i in range(len(chordListIn)):
        chordList = []
        list = chordListIn[i].pitches
        if len(list) >= 3:
            for x in range(len(list)):
                if list[x].name in chordList:
                    continue
                else:
                    chordList.append(list[x].name)
            
            if len(returnList) > 0 and all(z in chordList for z in returnList[len(returnList)-1]):
                continue
            else:
                es = analysis.enharmonics.EnharmonicSimplifier(chordList)
                chordList = es.bestPitches()
                returnList.append(chord.Chord(chordList))
                    
    return returnList

def removeInversion(tempChord):
    if "2" in tempChord:
        tempChord = tempChord.replace("2", "")
            
    if "3" in tempChord:
         tempChord = tempChord.replace("3", "")
            
    if "4" in tempChord:
        tempChord = tempChord.replace("4", "")      
              
    if "5" in tempChord:
        tempChord = tempChord.replace("5", "")
                    
    if "6" in tempChord:
        tempChord = tempChord.replace("6", "")
          
    return tempChord

def simplify_roman_name(roman_numeral):
    # Chords can get nasty names as "bII#86#6#5",
    # in this method we try to simplify names, even if it ends in
    # a different chord to reduce the chord vocabulary and display
    # chord function clearer.
    ret = roman_numeral.romanNumeral
    inversion_name = None
    inversion = roman_numeral.inversion()
    
    # Checking valid inversions.
    if ((roman_numeral.isTriad() and inversion < 3) or
            (inversion < 4 and
                 (roman_numeral.seventh is not None or roman_numeral.isSeventh()))):
        inversion_name = roman_numeral.inversionName()
        
    if (inversion_name is not None):
        ret = ret + str(inversion_name)
        
    elif (roman_numeral.isDominantSeventh()): ret = ret + "M7"
    elif (roman_numeral.isDiminishedSeventh()): ret = ret + "o7"
    return ret

def getHarmony(chords, key):
    chordList = []
    
    chords = cleanChords(chords)
    
    chord1 = None
    for i in range(len(chords)):
        chordAdd = removeInversion(simplify_roman_name(roman.romanNumeralFromChord(chords[i], key)))
        
        if chordAdd != chord1:
            chordList.append(chordAdd)
        chord1 = chordAdd
      
    #returnList = []
    #chord1 = None
    #for x in chordList:
    #    if x != chord1:
    #        returnList.append(x)
    #    chord1 = x
    return chordList  

def check_for_repetition(chords):
    for i in range(len(chords)):
        if chords[i] > 1:
            return True
    return False

def find_common_progressions(chordDict):
    keyList = []
    chordsList = []
    
    for i in range(len(chordDict["Number"])):
        if chordDict["Number"][i] == max(chordDict["Number"]):
            keyList.append(i)
                
    for x in range(len(keyList)):
        chordsList.append(chordDict["Progression"][keyList[x]])
            
    return chordsList

def check_for_progressions(chords):

    chordDict = {"Progression": [], "Number": []};
    chordDict["Number"].append(2)
    DictList = []
        
    for x in range(len(chords)):
        DictList.append({"Progression": [], "Number": []})

    DictList[0]["Number"].append(2)
    count = 0
    progression = ""
        
    while(check_for_repetition(DictList[count]["Number"])):
        count = count + 1
        for i in range(len(chords)-count):
            for x in range(count):
                if (i+x) >= len(chords):
                    break
                else:
                    progression = progression + " " +chords[i+x]
                
            if progression in DictList[count]["Progression"]:
                DictList[count]["Number"][DictList[count]["Progression"].index(progression)] = DictList[count]["Number"][DictList[count]["Progression"].index(progression)] + 1
                progression = ""
            else:
                DictList[count]["Progression"].append(progression)
                DictList[count]["Number"].append(1)
                progression = ""
            
    return find_common_progressions(DictList[count-1])


#print(cleanChords(open_midi("lmd/lmd_aligned/W/O/L/TRWOLRE128F427D710/03b77bd9334f18bddff53535fe6ca953.mid", True)))
chords = getHarmony(open_midi("TestMidis/NoSurprisesFull.mid", True), getKey("TestMidis/NoSurprisesFull.mid"))
#print(chords)
 
print(check_for_progressions(chords))
