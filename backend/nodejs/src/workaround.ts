const fs = require('fs');

const regex = new RegExp(/ else if \(core_1\.ContentSerdes\.get\(\)\.getSupportedMediaTypes\(\)\.indexOf\(core_1\.ContentSerdes\.getMediaType\(contentType\)\) < 0\) {\s+res\.writeHead\(415\);\s+res\.end\("Unsupported Media Type"\);\s+return \[2\];\s+}/gm);

let newLines = ' // else if (core_1.ContentSerdes.get().getSupportedMediaTypes().indexOf(core_1.ContentSerdes.getMediaType(contentType)) < 0) {\n' +
    '                            //     res.writeHead(415);\n' +
    '                            //     res.end("Unsupported Media Type");\n' +
    '                            //     return [2];\n' +
    '                            // }';

let filePath = `${__dirname}/../node_modules/@node-wot/binding-http/dist/http-server.js`;

fs.readFile(filePath, (error: any, data: any) => {
    if (error) {
        return console.error(error);
    }
    let result = data.toString().replace(regex, newLines);
    fs.writeFile(filePath, result, (error: any) => {
        if (error) {
            return console.error(error);
        }
    })
})
