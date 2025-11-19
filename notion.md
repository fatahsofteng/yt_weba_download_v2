# YouTube crawler automates audio file downloading (Youtube爬蟲自動化下載音檔)

## 1. Task Introduction:

- Please follow the channel list file to download all the videos in each channel, and record the metadata of the videos, so that we can carry out the subsequent ASR correction and training process.

## **1.1 Task Overview**

 The purpose of this task is to **automate** the process of **capturing audio and metadata of all videos from multiple YouTube channels in a batch** for subsequent **ASR calibration, audio dataset creation, TTS/VC training, and data cleansing**.

 In the end, the system will automatically list all the public videos of the channel according to the channel URL in the "Channel List File":

1.  List all public videos of the channel
2.  Download the audio file of each movie
3.  Record complete metadata
4.  Apply audio formatting specifications
5.  Save files to a clean, traceable folder structure.

## 2. Task **Reference** Steps:

1.  Find a way to download the audio file of a specific movie from youtube (or just download the movie and convert it to just the audio file).
2.  Record the metadata of the movie, if necessary:
    1.  Movie ID, e.g. Jq7llIkbJeA ( https://www.youtube.com/watch?v=Jq7llIkbJeA)
    2.  The channel from which the movie originated from in the channel list file, e.g.: @joeman ( Jq7llIkbJeA from https://www.youtube.com/@joeman)
    3.  Audio file metadata, e.g. Codec, Sample Rate, Bit Rate, Channels, Duration, File Size.
3.  Save the audio file and name it Video ID for easy tracking and management of the audio file, and save the metadata as {Video ID}.json for easy tracking.
4.  Please make sure to follow the below principles for audio file format:
    1.  Try to download uncompressed audio file format (but not mandatory because YT has already compressed it once), such as: WAV, FLAC, etc.
    2.  Sample Rate should be at least 16k.
    3.  If the number of channels is not mono, convert to Mono and save the file (if the multichannel is a separate track with a speaker, then please don't convert to Mono and keep the multichannel format).

### Resources:

1.  11/18 Provided by: v1 Channel List
    
    [創用CC_50個YT頻道.txt](attachment:3ce6d930-dab6-4436-b505-3e9d96508d91:創用CC_50個YT頻道.txt)
    
2.  3rd party API + google official streaming download link demo code:
    
    [https://drive.google.com/file/d/1yrSli8OZiOYdJH4VuMOBuqUdpVGIGCO_/view?usp=drive_link](https://www.notion.so/2af73351e87380898e1fd0e02cbe18d5?pvs=21) 
    

## **3. 🎯 Core Tasks**

### **###3. 🎯 Core Tasks**

### **3.1 Downloading audio files (Audio Download)**

 ✔ Follow each video URL

 ✔ Prioritize downloads in high quality, uncompressed formats (if provided by the platform)

 ✔ If only compressed audio files are available, download the highest bit rate version

 ✔ Audio file format must be m4a, sample rate = 44kHz

 Select a tool (choose one):

| **Tools** | **Pros** | **Disadvantages of the tool** |
| --- | --- | --- |
| **yt-dlp (recommended)** |  Stable, high speed, flexible format selection, cookies support, automatic sound quality optimization |  No official API |
|  YouTube API + yt-dlp |  API for more reliable information |  API quota limit |
|  puppeteer / playwright + yt-dlp |  Crawls cloaked channels |  Most complex |
|  3rd party API + google official streaming download link |  API is more reliable to get information |  To be tested |

### The tool is available for testing:

1.  3rd party API + google official streaming download link:
    
    https://drive.google.com/file/d/1yrSli8OZiOYdJH4VuMOBuqUdpVGIGCO_/view?usp=drive_link
    

---

## **3.2 📦 Metadata recording specification (video + audio)**

 One output per movie:

```
{video_id}.json
```

 Contents include:

### **① video metadata (Video Metadata)**

```
{
  "video_id": "Jq7llIkbJeA",
  "channel_url": "https://www.youtube.com/@joeman",
  ...
}
```

### **② audio metadata (Audio Metadata)**

```
{
  "codec": "opus",
  "sample_rate": 48000,
  "bit_rate": 160000,
  "channels": 2,
  "duration_sec": 512.23,
  "file_size": 32_123_442ㄆ
}
```

---

## **① Video Metadata ② Audio Metadata ① Video Metadata ① Audio Metadata ① Audio Metadata**

## **3.3 Audio Format Requirements**

### **⭕ Compulsory (mandatory)**

1. **Sample Rate == 44 kHz (44k or 48k recommended)**
2. **If the non-speaker is separated from the multi-track, convert all to Mono.**

**Output filename = video ID, e.g.:**

```
Jq7llIkbJeA.m4a
```

### **⭕ not mandatory, but preferred**

- If available in **uncompressed format (WAV) or lossless (FLAC)** → select the highest quality.
- If you can only download Opus/AAC → download the highest bit rate version (but without downloading too high quality audio files, try to **have a Sample Rate < 48 kHz** )