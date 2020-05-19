const express = require('express');

let app = express();
const directory = '/' + (process.env.STATIC_DIR || 'dist')
app.use(express.static(__dirname + directory));

let port = process.env.PORT || 3000;
app.listen(port, function () {
  console.log('Listening on', port);
});
