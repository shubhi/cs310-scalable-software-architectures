//
// app.post('/image/:userid', async (req, res) => {...});
//
// Uploads an image to the bucket and updates the database,
// returning the asset id assigned to this image.
//
const photoapp_db = require('./photoapp_db.js')
const { PutObjectCommand } = require('@aws-sdk/client-s3');
const { photoapp_s3, s3_bucket_name, s3_region_name } = require('./photoapp_s3.js');

const uuid = require('uuid');

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

exports.post_image = async (req, res) => {

  console.log("**Call to post /image/:userid...");

  try {

    // let data = req.body;  // data => JS object

    // throw new Error("TODO: /image");
    const { userid } = req.params;
    const { assetname, data } = req.body;  // base64 image string and assetname

    // Check if the user exists in the database
    const checkUserSql = `SELECT bucketfolder FROM users WHERE userid = '${userid}';`;
    const userResult = await query_database(photoapp_db, checkUserSql);

    if (userResult.length === 0) {
      return res.status(400).json({
        "message": "no such user...",
        "assetid": -1
      });
    }

    const bucketFolder = userResult[0].bucketfolder;

    // Generate a unique name for the asset
    const uniqueAssetName = uuid.v4() + ".jpg";
    const s3Key = `${bucketFolder}/${uniqueAssetName}`;

    // Decode the base64 string to get binary data
    const imageBuffer = Buffer.from(data, 'base64');

    // Prepare S3 upload parameters
    const s3Params = {
      Bucket: s3_bucket_name,
      Key: s3Key,
      Body: imageBuffer,
      ContentType: 'image/jpeg',
      ACL: 'public-read'
    };

    // Upload the image to S3
    const uploadCommand = new PutObjectCommand(s3Params);
    await photoapp_s3.send(uploadCommand);
    console.log(`Uploaded image to S3: ${s3Key}`);

    // Insert the asset into the assets table in the database
    const insertAssetSql = `
      INSERT INTO assets (userid, assetname, bucketkey)
      VALUES ('${userid}', '${assetname}', '${s3Key}');
    `;
    const insertResult = await query_database(photoapp_db, insertAssetSql);

    // Return success response with the asset ID
    if (insertResult.affectedRows === 1) {
      const assetid = insertResult.insertId;
      return res.status(200).json({
        "message": "success",
        "assetid": assetid
      });
    }
    else {
      throw new Error("Failed to insert asset into the database");
    }  
	
  }//try
  catch (err) {
    console.log("**Error in /image");
    console.log(err.message);
    
    res.status(500).json({
      "message": err.message,
      "assetid": -1
    });
  }//catch

}//post
