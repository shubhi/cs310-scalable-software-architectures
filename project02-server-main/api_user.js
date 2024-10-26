//
// app.put('/user', async (req, res) => {...});
//
// Inserts a new user into the database, or if the
// user already exists (based on email) then the
// user's data is updated (name and bucket folder).
// Returns the user's userid in the database.
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


exports.put_user = async (req, res) => {

  console.log("**Call to put /user...");

  try {

    let data = req.body;  // data => JS object

    console.log(data);

    // throw new Error("TODO: /user");
    
    const { email, lastname, firstname, bucketfolder } = data;

    // Check if all required fields are provided
    if (!email || !lastname || !firstname || !bucketfolder) {
      return res.status(400).json({
        "message": "Missing required fields: email, lastname, firstname, bucketfolder",
        "userid": -1
      });
    }

    // Escape variables to prevent SQL injection
    const escapedEmail = email;
    const escapedLastName = lastname;
    const escapedFirstName = firstname;
    const escapedBucketFolder = bucketfolder;

    // Query to check if the user already exists
    const checkUserSql = `
    SELECT userid FROM users WHERE email = '${escapedEmail}';`;
    const checkUserResults = await query_database(photoapp_db, checkUserSql);

    console.log(checkUserResults);

    if (checkUserResults.length === 0) {
      // User does not exist, insert new user
      const insertUserSql = `
        INSERT INTO users (email, lastname, firstname, bucketfolder)
        VALUES ('${escapedEmail}', '${escapedLastName}', '${escapedFirstName}', '${escapedBucketFolder}');
      `;
      const insertResult = await query_database(photoapp_db, insertUserSql);

      if (insertResult.affectedRows === 1) {
        return res.status(201).json({
          "message": "inserted",
          "userid": insertResult.insertId
        });
      } else {
        throw new Error("Failed to insert user");
      }
    } else {
      // User exists, update their info
      const updateUserSql = `
        UPDATE users
        SET lastname = '${escapedLastName}', firstname = '${escapedFirstName}', bucketfolder = '${escapedBucketFolder}'
        WHERE email = '${escapedEmail}';
      `;
      const updateResult = await query_database(photoapp_db, updateUserSql);

      if (updateResult.affectedRows === 1) {
        return res.status(200).json({
          "message": "updated",
          "userid": checkUserResults[0].userid
        });
      } else {
        throw new Error("Failed to update user");
      }
    }
	
  }//try
  catch (err) {
    console.log("**Error in /user");
    console.log(err.message);

    res.status(500).json({
      "message": err.message,
      "userid": -1
    });
  }//catch

}//put
