#! /usr/bin/python3

# Import libraries
import datetime
import os
import feedparser
import lxml.html
import urllib
from rich import print
from rich.console import Console
import time
import ssl

# Time the processing
startTime = time.time()

# Clear the screen whenever the script is run
console = Console()
console.clear()

# Variables to store RSS feed URI and path to mkdocs folder
feedLink = "https://latenightlinux.com/feed/mp3"
basePath = '.'
showSlug = 'LateNightLinuxMkDocsV2/docs'
confFilePath = 'LateNightLinuxMkDocsV2/mkdocs.yml'
buildCmd = './buildSite.sh'

# List all currently generated MD files to determine if all episodes need to be processed
def listMdFiles():
    mdFiles = []
    dirList = os.listdir(os.path.join(basePath,showSlug))    
    for dirObject in dirList:
        if os.path.isdir(os.path.join(basePath,showSlug,dirObject)):
            fileList = os.listdir(os.path.join(basePath,showSlug,dirObject))
            for file in fileList:
                if os.path.isfile(os.path.join(basePath,showSlug,dirObject,file)):
                    if os.path.splitext(os.path.join(basePath,showSlug,dirObject,file))[1] == ".md":
                        mdFiles.append(os.path.splitext(file)[0])
    return mdFiles

# Generate, from the site's HTML a string to represent the title and one to represent the meta description contents
def readMetaAndTitle(uri):
    #Load the HTML from the defined uri
    try:
        req = urllib.request.Request(uri,data=None,headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'})
        data = urllib.request.urlopen(req)
        data = data.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        print(f"[red]\t\t\tError opening: {error} - {uri}")
        return {"title":"","description":""}
    except urllib.error.URLError as error:
        print(f"[red]\t\t\tError opening: {error} - {uri}")
        return {"title":"","description":""}
    except ssl.SSLError as error:
        print(f"[red]\t\t\tError opening: {error} - {uri}")
        return {"title":"","description":""}
    #Parse the HTML using the lxml libraries
    pageHtml = lxml.html.fromstring(data)

    #Return the titles and format into a string
    titles = pageHtml.xpath("//title")
    titleString = ""
    for title in titles:
        if type(title.text) == type(""):
            titleString += title.text.strip()

    #Return the meta tags with the attribute name of description
    metaDescriptions = pageHtml.xpath("//meta[@name = 'description']")
    metaDescriptionString = ""
    for metaDescription in metaDescriptions:
        if "content" in metaDescription.attrib and metaDescription.attrib["content"] != "":
            if type(metaDescription.attrib["content"]) == type(""):
                tempString = metaDescription.attrib["content"].replace("\n"," - ")
                metaDescriptionString += tempString
    return {"title":titleString,"description":metaDescriptionString}

def processDiscoveries(paragraph):
    discoLinkList = []
    print(paragraph.getnext())

    links = paragraph.getchildren()
    print(links)
    for child in links:
        if child.tag == "a":
            discoveryText = child.text
            discoveryLink = child.attrib["href"]
            discoveryDetails = readMetaAndTitle(discoveryLink)
            if discoveryDetails["title"] == "" and discoveryDetails["description"] == "":
                discoveryDetails = readMetaAndTitle(discoveryLink)
            if discoveryDetails["title"] == "" and discoveryDetails["description"] == "":
                discoveryDetails = readMetaAndTitle(discoveryLink)    
            discoLink = {"text":discoveryText, "link":discoveryLink, "linkTitle":discoveryDetails["title"], "linkMetaDescription": discoveryDetails["description"]}
    return discoLinkList

# Load the RSS feed and create an empty dictionary and list to store episode details
feed = feedparser.parse(feedLink)
episodeAndLinks = {}
episodes = []

print("[yellow]Calculating already processed episodes...")
processedEpisodes = listMdFiles()

# Write the index file and include a modification date
print("[yellow]Writing index file...")
indexFile = open(os.path.join(basePath, showSlug, 'index.md'), "w")
indexFile.write("# Late Night Linux Discoveries"+os.linesep)
indexFile.write(os.linesep)
indexFile.write("Please use the links in the menu to view discoveries from each of the relevant episodes."+os.linesep)
indexFile.write(os.linesep)
indexFile.write("Generated on: " + datetime.datetime.now().strftime("%d/%m/%Y"))
indexFile.close()

# Rewrite the mkdocs.yml file to change the site version
# Read in all lines and amend the version
confFile = open(confFilePath, 'r')
confLines = []
for line in confFile:
    if 'version:' in line:
        #Process the line
        updatedLine = f'    version: {datetime.datetime.now().strftime("%Y-%m-%d")}'
        confLines.append(updatedLine)
    else:
        confLines.append(line)
confFile.close()
# Open the file and write the lines
confFile = open(confFilePath,"w")
for line in confLines:
    confFile.write(line)
confFile.close()

# Iterate through each episode and work out which ones have discoveries
# detail the discoveries and add to a list / dictionary
print("[yellow]Iterating through episodes...")
count = 0
for episode in feed.entries:
    discoLinkList = []
    episodeName = episode.title
    episodeLink = episode.link
    print(f"[blue]\t{episode.title}")
    # Ignore if the episode has already got an MD file associated with it
    if episodeName in processedEpisodes:
        print("[green]\t\tAlready processed. Ignoring")
    else:
        # Process episodes if an MD file does not exist for it
        episodePublished = datetime.datetime.strptime(episode.published, "%a, %d %b %Y %H:%M:%S +0000")
        episodePublishedString = datetime.datetime.strptime(episode.published, "%a, %d %b %Y %H:%M:%S +0000").strftime("%d/%m/%Y")

        # Find the rows in the encoded content that referencies <strong>Discoveries and the next tag of strong
        pageHtml = lxml.html.fromstring(episode.content[0].value)
        paragraphs = pageHtml.xpath("//p")
        lowCount = -1
        highCount = -1
        counter = 0
        print(f"[green]\t\tFinding discoveries")
        for paragraph in paragraphs:
            if len(paragraph) > 0:
                paragraph = paragraph.getchildren()[0]
                if paragraph.tag == "strong":
                    if type(paragraph.text) == type("") and 'Discoveries' in paragraph.text:
                        lowCount = counter
                        #discoLinkList = processDiscoveries(paragraph)
                        #pass
                    elif lowCount > -1:
                        highCount = counter
                        break
            counter += 1

        # Now print discoveries, using the values from the previous loop
        print(f"[green]\t\tWorking out details from the link")
        for i in range(lowCount, highCount):
            a = paragraphs[i].getchildren()
            for child in a:
                if child.tag == "a":
                    discoveryText = child.text
                    discoveryLink = child.attrib["href"]
                    discoveryDetails = readMetaAndTitle(discoveryLink)
                    if discoveryDetails["title"] == "" and discoveryDetails["description"] == "":
                        discoveryDetails = readMetaAndTitle(discoveryLink)
                    if discoveryDetails["title"] == "" and discoveryDetails["description"] == "":
                        discoveryDetails = readMetaAndTitle(discoveryLink)    
                    discoLink = {"text":discoveryText, "link":discoveryLink, "linkTitle":discoveryDetails["title"], "linkMetaDescription": discoveryDetails["description"]}
                    discoLinkList.append(discoLink)
        if len(discoLinkList) > 0:
            episodes.append({'episodeName': episodeName, 'episodeLink': episodeLink, 'episodePublished': episodePublished,
                            'episodePublishedString': episodePublishedString, 'discoLinkList': discoLinkList})

# Now, write some files into a directory structure, detailing the links inside
# Create the base directory if it doesn't exist
if not (os.path.isdir(os.path.join(basePath, showSlug))):
    os.mkdir(os.path.join(basePath, showSlug))

print("[yellow]Writing MD files and directories")
for episode in episodes:
    # Create a folder for each year within the feed
    if not (os.path.isdir(os.path.join(basePath, showSlug, str(episode['episodePublished'].year)))):
        os.mkdir(os.path.join(basePath, showSlug,
                 str(episode['episodePublished'].year)))
    # Create a file for each episode
    fw = open(os.path.join(basePath, showSlug, str(
        episode['episodePublished'].year), episode['episodeName']+'.md'), 'w')

    # Write the contents to the MD files
    # Write the header
    fw.write("# " + episode['episodeName']+os.linesep)
    # Add a link to the episode
    fw.write("Episode Link: ["+episode['episodeLink'] + "](" + episode['episodeLink']+")  "+os.linesep)
    # Add the release date
    fw.write("Release Date: "+episode['episodePublishedString']+os.linesep)
    # Add the discoveries title
    fw.write("## Discoveries"+os.linesep+os.linesep)
    # Add a table detailing all discoveries for the episode
    fw.write(f'| Name and Link | Page Title | Page Description |{os.linesep}')
    fw.write('| ----- | ----- | ----- |'+os.linesep)
    for disco in episode['discoLinkList']:
        fw.write(f"| [{disco['text']}]({disco['link']}) | {disco['linkTitle']} | {disco['linkMetaDescription']} |{os.linesep}")
    fw.write(os.linesep)
    # Write the generated on information
    fw.write("Generated on: " + datetime.datetime.now().strftime("%d/%m/%Y"))
    fw.close()
    print('[red]\tWritten file for...', episode['episodeName'])    

print('[yellow]Generating site...')
os.system(buildCmd)

endTime = time.time()
print(f"Time taken to run: {round(endTime-startTime,0)}s")