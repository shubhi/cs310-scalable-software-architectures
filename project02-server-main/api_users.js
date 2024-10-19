//
// app.get('/users', async (req, res) => {...});
//
// Return all the users from the database:
//
const photoapp_db = require('./photoapp_db.js')


//
// query_database:
//
// Queries database, returning a PROMISE that you can
// await on. When the PROMISE resolves, you'll have the 
// results of your query (or you'll get an error thrown
// back).
//
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


//
// get /users:
//
exports.get_users = async (req, res) => {

  console.log("**Call to get /users...");

  try {

    //
    // query to select all users from user table in ascending order by user id
    //
    let sql = `SELECT * FROM users ORDER BY userid ASC;`;
    console.log("/users: calling RDS to get user table...");
    let mysql_promise = query_database(photoapp_db, sql);
    let results = await Promise.all([mysql_promise]);
    let rds_results = results[0];
    
    //
    // done, respond with users table:
    //
    console.log("/users done, sending response...");
    res.json({
      "message": "success",
      "data": rds_results
    });
  }//try
  catch (err) {
    console.log("**Error in /users");
    console.log(err.message);
    
    res.status(500).json({
      "message": err.message,
      "data": []
    });
  }//catch

}//get
