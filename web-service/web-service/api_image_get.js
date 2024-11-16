 //
// app.get('/image/:assetid', async (req, res) => {...});
//
// downloads an asset from S3 bucket and sends it back to the
// client as a base64-encoded string.
//
const photoapp_db = require('./photoapp_db.js')
const { GetObjectCommand } = require('@aws-sdk/client-s3');
const { photoapp_s3, s3_bucket_name, s3_region_name } = require('./photoapp_s3.js');

function query_database(db, sql)
{
  let response = new Promise((resolve, reject) => {
    try 
    {
      //
      // execute the query, and when we get the callback from
      // the database server, either resolve with the results
      // or error with the error object
      //
      db.query(sql, (err, results, _) => {
        if (err) {
          reject(err);
        }
        else {
          resolve(results);
        }
      });
    }
    catch (err) {
      reject(err);
    }
  });
  
  // 
  // return the PROMISE back to the caller, which will
  // eventually resolve to results or an error:
  //
  return response;
}

async function getobject_database(bucket, key) {
  const input = {
    "Bucket": bucket,
    "Key": key
  };
  const command = new GetObjectCommand(input);
  
  try {
    const response = await photoapp_s3.send(command);
    /* response ==
    {
      "AcceptRanges": "bytes",
      "ContentLength": "10",
      "ContentRange": "bytes 0-9/43",
      "ContentType": "text/plain",
      "ETag": "\"0d94420ffd0bc68cd3d152506b97a9cc\"",
      "LastModified": "Thu, 09 Oct 2014 22:57:28 GMT",
      "Metadata": {},
      "VersionId": "null"
    }*/

    var datastr = await response.Body.transformToString("base64");
  
    return datastr;
  } 
  
  catch (error) {
    console.error("Error fetching object from S3: ", error);
    throw error; // rethrow the error after logging if needed
  }
}


exports.get_image = async (req, res) => {

  console.log("**Call to get /image/:assetid...");

  try {
    // throw new Error("TODO: /image/:assetid");

    //
    // TODO
    //
    // MySQL in JS:
    //   https://expressjs.com/en/guide/database-integration.html#mysql
    //   https://github.com/mysqljs/mysql
    // AWS:
    //   https://docs.aws.amazon.com/sdk-for-javascript/v3/developer-guide/javascript_s3_code_examples.html
    //   https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/clients/client-s3/classes/getobjectcommand.html
    //   https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/clients/client-s3/

    let assetid = req.params.assetid;

    sql = `
    SELECT a.userid, a.assetname, a.bucketkey
    FROM assets a
    WHERE assetid LIKE '${assetid}';`;
    
    console.log("/assets: calling RDS to get user table...");
    mysql_promise = query_database(photoapp_db, sql);
    results = await Promise.all([mysql_promise]);

    if (results[0].length === 0) {
      console.log(`**Invalid assetid: ${assetid}`);
      return res.status(400).json({
        "message": `No such asset...`,
        "user_id": -1,
        "asset_name": "?",
        "bucket_key": "?",
        "data": []
      });
    }
    else 
    {
      rds_results = results[0][0];

      let user_id = rds_results.userid;
      let asset_name = rds_results.assetname;
      let bucket_key = rds_results.bucketkey;

      let data = await getobject_database(s3_bucket_name, bucket_key);

      console.log("/users done, sending response...");
      res.json({
        "message": "success",
        "user_id": user_id,
        "asset_name": asset_name,
        "bucket_key": bucket_key,
        "data": data
      });
    }

  }//try
  catch (err) {
    console.log("**Error in /image");
    console.log(err.message);
    
    res.status(500).json({
      "message": err.message,
      "user_id": -1,
      "asset_name": "?",
      "bucket_key": "?",
      "data": []
    });
  }//catch

}//get