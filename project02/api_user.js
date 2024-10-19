//
// app.put('/user', async (req, res) => {...});
//
// Inserts a new user into the database, or if the
// user already exists (based on email) then the
// user's data is updated (name and bucket folder).
// Returns the user's userid in the database.
//
const photoapp_db = require('./photoapp_db.js')

exports.put_user = async (req, res) => {

  console.log("**Call to put /user...");

  try {

    let data = req.body;  // data => JS object

    console.log(data);

    throw new Error("TODO: /user");
    
	
	
	
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
