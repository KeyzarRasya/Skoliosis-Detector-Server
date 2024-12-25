const express = require("express")
const multer = require('multer')
const cors = require('cors')

const app = express()

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, 'uploads/')
    },
    filename: (req, file, cb) => {
        cb(null, `${Date.now()}-${file.originalname}`)
    }
})

const upload = multer({storage})

app.use(express.urlencoded({extended:true}))
app.use(express.json())
app.use(cors())

app.get("/", (req, res) => [
    console.log("Hello!")
])

app.post("/api/upload", upload.array('demo[]'), (req, res) => {
    console.log(req.files)
    res.status(200).send({message:"Success Upload", file:req.files})
})

app.listen(3000, () => {
    console.log("Connected to server PORT 3000")
})