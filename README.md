# ntap_gather_data
A project to gather data from a NTAP to help size Rubrik.

The idea behind this project is to attempt to automate data gathering on a NTAP array for NAS sizing on a Rubrik.
The script uses API calls on the NTAP to discover NAS volumes across SVMs and reports back the used logical space as well as the number of files in each NAS volume.  It then generates totals for each SVM as well a summary worksheet for the entire array.
For the purposes of this script a NAS volume is a volume that does not contain a LUN.  This behavior can be over-ridden with the -a flag

This script uses 2 non-stanedard Python libraries.  Both are included in the repo and the script is built to use them in-place.  One is for the NTAP API and the other is to build the spreadsheet.  If you want to install them elsewhere and tweak the script for your site, feel free.

I have tested the script in Python 2.7 and 3.7.4.  Other versions may work but I haven't tested them.  Let me know if some version of 3.x doesn't work.  I'm not too concerned with supporting earlier than 2.7 at this time since Python 2 is EOL in 2020.

<h3>Authentication</h3>
The NTAP API requires creentials.  The simplest way to handle this is to allow the script to prompt the user.  If the goal is to run non-interactively, there are 3 options.  The first is to simnply hard code them into the script.  The variabled 'user' and 'password' are initialized as empty strings.  You can change that if you like.
The other 2 involve the -c flag.  The -c flag takes one of two arguments.  The first is simply 'user:password'.  This obviously puts the credentials in plaintext on the command line, but it works.  
The other is to store the credentials in a obfuscated file on the client.  In this case argument to the -c flag is the name of the file.  The file is expected to be in the format created by my 
<a href="https://github.com/adamrfox/creds_encode">creds_encode script</a>.  It's not the most secure but that and locking the file down with permissions may be acceptable to some sites.

<pre>
Usage: ntap_gather_data.py [-ha] [-c creds] ntap output_file
-h | --help  : Prints Usage
-a | -all    : Include all volume.  By default, volumes with LUNs are excluded
-c | --creds : Put NTAP credentials on the command line.  Either user:pwd or creds file
   See README for details on creds file.
ntap: Name or IP of the NTAP Cluster Management Port
output_file: File to output. Format is MicroSoft XLSX
</pre>
