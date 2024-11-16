//
// app.get('/bucket?startafter=bucketkey', async (req, res) => {...});
//
// Retrieves the contents of the S3 bucket and returns the 
// information about each asset to the client. Note that it
// returns 12 at a time, use startafter query parameter to pass
// the last bucketkey and get the next set of 12, and so on.
//
const { ListObjectsV2Command } = require('@aws-sdk/client-s3');
const { photoapp_s3, s3_bucket_name, s3_region_name } = require('./photoapp_s3.js');

exports.get_bucket = async (req, res) => {

  console.log("**Call to get /bucket...");

  try {

    
    // throw new Error("TODO: /bucket/?startafter=bucketkey");

    //
    // TODO: remember, 12 at a time...  Do not try to cache them here, instead 
    // request them 12 at a time from S3
    //
    // AWS:
    //   https://docs.aws.amazon.com/sdk-for-javascript/v3/developer-guide/javascript_s3_code_examples.html
    //   https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/clients/client-s3/classes/listobjectsv2command.html
    //   https://docs.aws.amazon.com/AWSJavaScriptSDK/v3/latest/clients/client-s3/
    //
    
    // Get 'startafter' query parameter if it exists
    const startAfter = req.query.startafter || null;

    // Set up input for ListObjectsV2Command
    const input = {
      Bucket: s3_bucket_name,
      MaxKeys: 12, // Limit the response to 12 objects
    };

    // If 'startafter' query param is provided, include it in the input
    if (startAfter) {
      input.StartAfter = startAfter;
    }

    // Create and send the command to S3
    const command = new ListObjectsV2Command(input);
    const response = await photoapp_s3.send(command);

    // Check how many keys were returned
    const keyCount = response.KeyCount || 0;

    // Log response for debugging
    console.log(`Fetched ${keyCount} keys from S3`);

    // If no objects are returned, respond with an empty array
    if (keyCount === 0) {
      return res.status(200).json({
        message: "success",
        data: [],
      });
    }

    // Send the objects information back to the client
    res.status(200).json({
      message: "success",
      data: response.Contents, // This contains the array of object metadata
    });

  }//try
  catch (err) {
    console.log("**Error in /bucket");
    console.log(err.message);
    
    res.status(500).json({
      "message": err.message,
      "data": []
    });
  }//catch

}//get
