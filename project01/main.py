#
# Main program for photoapp program using AWS S3 and RDS to
# implement a simple photo application for photo storage and
# viewing.
#
# Authors:
#   Shubhi Gupta
#   Prof. Joe Hummel (initial template)
#   Northwestern University
#

import datatier  # MySQL database access
import awsutil  # helper functions for AWS
import boto3  # Amazon AWS

import uuid
import pathlib
import logging
import sys
import os

from configparser import ConfigParser

import matplotlib.pyplot as plt
import matplotlib.image as img


###################################################################
#
# prompt
#
def prompt():
  """
  Prompts the user and returns the command number
  
  Parameters
  ----------
  None
  
  Returns
  -------
  Command number entered by user (0, 1, 2, ...)
  """

  try:
    print()
    print(">> Enter a command:")
    print("   0 => end")
    print("   1 => stats")
    print("   2 => users")
    print("   3 => assets")
    print("   4 => download")
    print("   5 => download and display")
    print("   6 => upload")
    print("   7 => add user")

    cmd = int(input())
    return cmd

  except Exception as e:
    print("ERROR")
    print("ERROR: invalid input")
    print("ERROR")
    return -1


###################################################################
#
# check if duplicate asset key exists in assets table
#
def check_duplicate_asset_key(userid, key):
    sql = f"""
    SELECT bucketkey FROM assets WHERE userid = '{userid}';
    """
    table = datatier.retrieve_all_rows(dbConn, sql)

    if key in table:
      return True
    else:
      return False
#
# check if duplicate bucket exists in user table
#
def check_duplicate_user_bucket(bucket):
    sql = f"""
    SELECT bucketfolder FROM users;
    """
    table = datatier.retrieve_all_rows(dbConn, sql)

    if bucket in table:
      return True
    else:
      return False
#
# check if user exists
#
def check_user(userid):
    sql = f"""
    SELECT userid FROM users WHERE userid = '{userid}';
    """
    table = datatier.retrieve_one_row(dbConn, sql)

    if userid in table:
      return True
    else:
      return False
#
# check if asset exists
#
def check_asset(assetid):
    sql = f"""
    SELECT assetid FROM assets WHERE assetid = '{assetid}';
    """
    table = datatier.retrieve_one_row(dbConn, sql)

    if assetid in table:
      return True
    else:
      return False


###################################################################
#
# stats
#
def stats(bucketname, bucket, endpoint, dbConn):
  """
  Prints out S3 and RDS info: bucket name, S3 assets, RDS, endpoint, # of users and # of assets in the database
  
  Parameters
  ----------
  bucketname: S3 bucket name,
  bucket: S3 boto bucket object,
  endpoint: RDS machine name,
  dbConn: open connection to MySQL server
  
  Returns
  -------
  nothing
  """
  #
  # bucket info:
  #
  try: 

    #S3 bucket name
    print("S3 bucket name:", bucketname)

    #S3 asset count
    assets = bucket.objects.all()
    print("S3 assets:", len(list(assets)))

    # MySQL info:
    print("RDS MySQL endpoint:", endpoint)

    # Count of users
    # query to select count of user id in users table
    sql = """
    SELECT COUNT(userid) from users;
    """
    row = datatier.retrieve_one_row(dbConn, sql)
    if row is None:
      print("Database operation failed...")
    elif row == ():
      print("Unexpected query failure...")
    else:
      print(f'# of users: {row[0]}')

    # Count of assets
    # query to select count of user id in users table
    sql = """
    SELECT COUNT(assetid) from assets;
    """
    row = datatier.retrieve_one_row(dbConn, sql)
    if row is None:
      print("Database operation failed...")
    elif row == ():
      print("Unexpected query failure...")
    else:
      print(f'# of assets: {row[0]}')

  except Exception as e:
    print("ERROR")
    print("ERROR: an exception was raised and caught")
    print("ERROR")
    print("MESSAGE:", str(e))

def users(bucketname, bucket, endpoint, dbConn):
  """
  Prints out Users info: userid, email, name and folder
  
  Parameters
  ----------
  bucketname: S3 bucket name,
  bucket: S3 boto bucket object,
  endpoint: RDS machine name,
  dbConn: open connection to MySQL server
  
  Returns
  -------
  nothing
  """
  try: 
    # query to select all users from user table in descending order by user id
    sql = """
    SELECT * FROM users ORDER BY userid DESC;
    """
    table = datatier.retrieve_all_rows(dbConn, sql)
    if table is None:
      print("Database operation failed...")
    elif table == ():
      print("Unexpected query failure...")
    else:
      # print for each user in the table
      for row in table:
        print(f'User id: {row[0]}')
        print(f'  Email: {row[1]}')
        print(f'  Name: {row[2]} , {row[3]}')
        print(f'  Folder: {row[4]}')

  except Exception as e:
    print("ERROR")
    print("ERROR: an exception was raised and caught")
    print("ERROR")
    print("MESSAGE:", str(e))


def assets(bucketname, bucket, endpoint, dbConn):
  """
  Prints out Asset info: Asset ID, User ID, Original file name and Key name
  
  Parameters
  ----------
  bucketname: S3 bucket name,
  bucket: S3 boto bucket object,
  endpoint: RDS machine name,
  dbConn: open connection to MySQL server
  
  Returns
  -------
  nothing
  """
  #
  # assets info:
  #
  try: 
    # query to select all assets from the asset table in descending order of assetid
    sql = """
    SELECT * FROM assets ORDER BY assetid DESC;
    """
    table = datatier.retrieve_all_rows(dbConn, sql)
    if table is None:
      print("Database operation failed...")
    elif table == ():
      print("Unexpected query failure...")
    else:
      # print for each asset in the table
      for row in table:
        print(f'Asset id: {row[0]}')
        print(f'  User id: {row[1]}')
        print(f'  Original name: {row[2]}')
        print(f'  Key name: {row[3]}')

  except Exception as e:
    print("ERROR")
    print("ERROR: an exception was raised and caught")
    print("ERROR")
    print("MESSAGE:", str(e))


def download(bucketname, bucket, endpoint, dbConn):
  """
  Retrieves asset from the database, downloads and renames it based on original file name
  
  Parameters
  ----------
  bucketname: S3 bucket name,
  bucket: S3 boto bucket object,
  endpoint: RDS machine name,
  dbConn: open connection to MySQL server
  
  Returns
  -------
  nothing
  """
  try: 

    print("Enter asset id>")
    assetid = int(input())

    if assetid is None:
      print("Invalid asset ID...")
    elif check_asset(assetid) is False:
      print(f"No such asset...")
    else:
      # query to select asset name and key from assests table for defined asset id
      sql = f"""
      SELECT a.assetname, a.bucketkey
      FROM assets a
      WHERE assetid LIKE '{assetid}';
      """
      row = datatier.retrieve_one_row(dbConn, sql)
      if row is None:
        print(f"Asset ' {assetid} ' does not exist ...")
      elif row == ():
        print("Unexpected query failure...")
      else:
        #extract assetname and key from query reow
        assetname = row[0]
        key = row[1]

        #download assest from S3 bucket
        download_status = awsutil.download_file_and_save(bucket, key, assetname)

        if download_status is not None:
          print(f'Downloaded from S3 and saved as \' {assetname} \'')

  except Exception as e:
    print("ERROR")
    print("ERROR: an exception was raised and caught")
    print("ERROR")
    print("MESSAGE:", str(e))

def download_and_display(bucketname, bucket, endpoint, dbConn):
  """
  Retrieves asset from the database, downloads and renames it based on original file name and also displays the file.
  
  Parameters
  ----------
  bucketname: S3 bucket name,
  bucket: S3 boto bucket object,
  endpoint: RDS machine name,
  dbConn: open connection to MySQL server
  
  Returns
  -------
  nothing
  """
  try: 

    print("Enter asset id>")
    assetid = int(input())

    if assetid is None:
      print("Invalid asset ID...")
    elif check_asset(assetid) is False:
      print(f"No such asset...")
    else:
      # query to extract assetname and key for defined assetid from assets table
      sql = f"""
      SELECT a.assetname, a.bucketkey
      FROM assets a
      WHERE assetid LIKE '{assetid}';
      """
      row = datatier.retrieve_one_row(dbConn, sql)

      if row is None:
        print(f"Asset ' {assetid} ' does not exist ...")
      elif row == ():
        print("Unexpected query failure...")
      else:
        #extract asset info from query row
        assetname = row[0]
        key = row[1]
      
        #download assest from S3 bucket
        download_status = awsutil.download_file_and_save(bucket, key, assetname)
        if download_status is not None:
          print(f'Downloaded from S3 and saved as \' {assetname} \'')

          # display image
          image = img.imread(assetname)
          plt.imshow(image)
          plt.show()

  except Exception as e:
    print("ERROR")
    print("ERROR: an exception was raised and caught")
    print("ERROR")
    print("MESSAGE:", str(e))

def upload(bucketname, bucket, endpoint, dbConn):
  """
  Uploads submitted image to S3 bucket and updates assets table
  
  Parameters
  ----------
  bucketname: S3 bucket name,
  bucket: S3 boto bucket object,
  endpoint: RDS machine name,
  dbConn: open connection to MySQL server
  
  Returns
  -------
  nothing
  """
  try: 

    #input local filename
    print("Enter local filename>")
    local_filename = str(input())

    if local_filename is None:
      print("Invalid file path.")
    elif not os.path.exists(local_filename):
      print("File not found")
    else:
      #input user id
      print("Enter user id>")
      userid = int(input())

      if userid is None:
        print("Invalid user id.")
      elif check_user(userid) is False:
        print(f"No such user ...")
      else:
        #query to extract bucket for userid from users table
        sql = f"""
        SELECT bucketfolder
        FROM users
        WHERE userid = '{userid}';
        """
        row = datatier.retrieve_one_row(dbConn, sql)

        if row is None:
          print(f"No such use ...")
        elif row == ():
          print("Unexpected query failure...")
        else:
          #extract user bucket folder from query row
          bucketfolder = row[0]

          #generate random key for asset
          extension = pathlib.Path(local_filename).suffix
          filename = str(uuid.uuid4()) + extension
          key = bucketfolder + "/" + filename

          #query to check if generated key already exists in assets
          while check_duplicate_asset_key(userid, key) is True:
            print("duplicate asset key")
            #generate random key for asset
            filename = str(uuid.uuid4()) + extension
            key = bucketfolder + "/" + filename

          #upload asset to s3
          upload_status = awsutil.upload_file(local_filename, bucket, key)
          if upload_status != -1:
            #query to update assets table with new asset info
            sql = f"""
              INSERT INTO assets(userid, assetname, bucketkey)
              values('{userid}','{local_filename}','{key}');
              """

            update_status = datatier.perform_action(dbConn, sql, parameters=[])
            if update_status != -1:
              print(f'Uploaded and stored in S3 as \' {key} \' ')

              # query to extract last updated asset id
              sql = f"""
                SELECT LAST_INSERT_ID();
                """
              row = datatier.retrieve_one_row(dbConn, sql)
              print(f'Recorded in RDS under asset id {row[0]}')


  except Exception as e:
    print("ERROR")
    print("ERROR: an exception was raised and caught")
    print("ERROR")
    print("MESSAGE:", str(e))

def add_user(bucketname, bucket, endpoint, dbConn):
  """
  Input user information such as email, first name, last name and updates to the user table
  
  Parameters
  ----------
  bucketname: S3 bucket name,
  bucket: S3 boto bucket object,
  endpoint: RDS machine name,
  dbConn: open connection to MySQL server
  
  Returns
  -------
  nothing
  """
  try: 

    # input user info
    print("Enter user's email>")
    email = str(input())
    if email is None:
      print("Invalid Email")
    else:
      print("Enter user's last (family) name>")
      last_name = str(input())
      if last_name is None:
        print("Invalid Last Name")
      else:
        print("Enter user's first (given) name>")
        first_name = str(input())
        if first_name is None:
          print("Invalid First Name")
        else:
          # generate new bucket for user
          bucketfolder = str(uuid.uuid4())

          #verify bucket does not already exist
          while check_duplicate_user_bucket(bucketfolder) is True:
            bucketfolder = str(uuid.uuid4())

          #query to update user into users table
          sql = f"""
          INSERT INTO 
          users(email, lastname, firstname, bucketfolder)
          values('{email}', '{last_name}', '{first_name}', '{bucketfolder}');
          """
        
          update_status = datatier.perform_action(dbConn, sql, parameters=[])

          if update_status != -1:
              # query to extract last updated user id
              sql = f"""
                SELECT LAST_INSERT_ID();
                """
              row = datatier.retrieve_one_row(dbConn, sql)
              print(f'Recorded in RDS under user id {row[0]}')

  except Exception as e:
    print("ERROR")
    print("ERROR: an exception was raised and caught")
    print("ERROR")
    print("MESSAGE:", str(e))


#########################################################################
# main
#
print('** Welcome to PhotoApp **')
print()

# eliminate traceback so we just get error message:
sys.tracebacklimit = 0

#
# what config file should we use for this session?
#
config_file = 'photoapp-config.ini'

print("What config file to use for this session?")
print("Press ENTER to use default (photoapp-config.ini),")
print("otherwise enter name of config file>")
s = input()

if s == "":  # use default
  pass  # already set
else:
  config_file = s

#
# does config file exist?
#
if not pathlib.Path(config_file).is_file():
  print("**ERROR: config file '", config_file, "' does not exist, exiting")
  sys.exit(0)

#
# gain access to our S3 bucket:
#
s3_profile = 's3readwrite'

os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file

boto3.setup_default_session(profile_name=s3_profile)

configur = ConfigParser()
configur.read(config_file)
bucketname = configur.get('s3', 'bucket_name')

s3 = boto3.resource('s3')
bucket = s3.Bucket(bucketname)

#
# now let's connect to our RDS MySQL server:
#
endpoint = configur.get('rds', 'endpoint')
portnum = int(configur.get('rds', 'port_number'))
username = configur.get('rds', 'user_name')
pwd = configur.get('rds', 'user_pwd')
dbname = configur.get('rds', 'db_name')

dbConn = datatier.get_dbConn(endpoint, portnum, username, pwd, dbname)

if dbConn is None:
  print('**ERROR: unable to connect to database, exiting')
  sys.exit(0)

#
# main processing loop:
#
cmd = prompt()

while cmd != 0:
  #
  if cmd == 1:
    stats(bucketname, bucket, endpoint, dbConn)
  elif cmd == 2:
    users(bucketname, bucket, endpoint, dbConn)
  elif cmd == 3:
    assets(bucketname, bucket, endpoint, dbConn)
  elif cmd == 4:
    download(bucketname, bucket, endpoint, dbConn)
  elif cmd == 5:
    download_and_display(bucketname, bucket, endpoint, dbConn)
  elif cmd == 6:
    upload(bucketname, bucket, endpoint, dbConn)
  elif cmd == 7:
    add_user(bucketname, bucket, endpoint, dbConn)
  else:
    print("** Unknown command, try again...")
  #
  cmd = prompt()

#
# done
#
print()
print('** done **')