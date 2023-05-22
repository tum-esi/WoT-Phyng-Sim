import {Servient} from '@node-wot/core';
import {HttpServer} from '@node-wot/binding-http';
import dotenv from 'dotenv';

import {CaseConstructorType, Simulator} from './base/simulator';
import {ChtCase} from './behavior/cht';
import {chtCdSchema} from './base/schemas';
import { AbstractThing } from './base/thing';
import { URL } from 'url';
import express from 'express';
import * as fs from 'fs'
import path from 'path';

import os from 'os'

dotenv.config({path: path.resolve(__dirname, '../.env')});

let CASE_PARAMS: CaseConstructorType = {
    'cht': {
        'constructor': (host: string, wot: WoT.WoT,
                        tm: WoT.ThingDescription, name: string) => new ChtCase(host, wot, tm, name),
        'tm': require('../tms/behavior/cht/chtCase.model.json'),
        'cdValidator': chtCdSchema
    }
}

let httpServer = new HttpServer({
    port: 8080,
    baseUri: process.env.BASE_URI
});
let servient = new Servient();
servient.addServer(httpServer);

servient.start()
    .then(async (WoT) => {
        let pythonHost: string = process.env.PYTHON_SERVER || 'http://127.0.0.1:5000';
        let simulator = new Simulator(pythonHost, WoT, require('../tms/simulator.model.json'), CASE_PARAMS);
    })

/**========================================================================
 *                           TM Models Server
 *========================================================================**/
let interfaces = os.networkInterfaces();
const PORT = 8081;
let expressURL = 'localhost'
if (process.env.BASE_URI) expressURL = process.env.BASE_URI
else if (interfaces && interfaces.eth0 && interfaces.eth0[0]) expressURL = interfaces['eth0'][0]['address']

const app = express()
app.get('/tms', async (req, res) => {
    let behaviorArray = []
    const dir = fs.opendirSync(path.join(__dirname, '..', 'tms', 'behavior'))
    for await (const dirent of dir) {
        if(dirent.isDirectory()) {
            let behaviorName = dirent.name
            let url = new URL(`${req.url}/${behaviorName}`,`http://${req.headers.host}`)
            behaviorArray.push(url)
        }
    }
    res.json(behaviorArray)
})

app.get('/tms/:behavior', async (req, res) => {
    let tmsArray = [];
    const dir = fs.opendirSync(path.join(__dirname, '..', 'tms', 'behavior'))
    for await (const dirent of dir) {
        if(dirent.isDirectory() && dirent.name == req.params.behavior) {
            const tmDir = fs.opendirSync(path.join(__dirname, '..', 'tms', 'behavior', dirent.name))
            for await(const tmFile of tmDir) {
                if(tmFile.isFile()) {
                   let tmName = path.basename(tmFile.name, '.model.json')
                   let url = new URL(`${req.url}/${tmName}`, `http://${req.headers.host}`)
                   tmsArray.push(url)
                }
            }
        }
    }
    res.json(tmsArray)
})

app.get('/tms/:behavior/:tmName', async (req, res) => {
    let extendedTm = {}
    const dir = fs.opendirSync(path.join(__dirname, '..', 'tms', 'behavior'))
    for await (const dirent of dir) {
        if(dirent.isDirectory() && dirent.name == req.params.behavior) {
            const tmDir = fs.opendirSync(path.join(__dirname, '..', 'tms', 'behavior', dirent.name))
            for await(const tmFile of tmDir) {
                if(tmFile.isFile() && tmFile.name.includes(req.params.tmName)) {
                    let tmString = fs.readFileSync(path.join(__dirname, '..', 'tms', 'behavior', dirent.name, tmFile.name), {encoding: 'utf-8'}) 
                    extendedTm = AbstractThing.extendTmByLink(JSON.parse(tmString));
                }
            }
        }
    }
    res.json(extendedTm)
})


app.listen(PORT, expressURL)
console.log(`Appilcation is listening at ${expressURL}:${PORT}`)
