/**
 * Case module.
 *
 * @file   Contains an AbstractCase class that is used as a base for all case types.
 * @author Anatolii Tsirkunenko
 * @since  29.11.2021
 */
import {AbstractThing} from './thing';
import {CaseParameters, PhyngHrefs, PhyngProps, PhysicalDescription} from './interfaces';
import {AbstractPhyng} from './phyng';
import {responseIsSuccessful, responseIsUnsuccessful} from './helpers';
import {reqGet, reqPost, reqPatch, makeRequest} from './axios-requests';
import {AxiosResponse} from 'axios';

const FormData = require('form-data');
const fs = require('fs');

/** Case commands allowed in the simulator. */
type CaseCommand = 'run' | 'stop' | 'setup' | 'clean' | 'postprocess' | 'time';

interface CaseTime {
    real: string,
    simulation: string,
    difference: number
}

/**
 * An abstract case.
 *
 * Abstract class used by all Web of Phyngs
 * simulation cases in this application.
 * @class AbstractCase
 * @abstract
 */
export abstract class AbstractCase extends AbstractThing implements CaseParameters {
    /** Case name. */
    protected _name: string;
    /** Case type. */
    protected _type: string = '';
    /** Case phyngs. */
    protected phyngs: { [name: string]: AbstractPhyng };
    /** Case mesh quality. */
    protected _meshQuality: number = 50;
    /** Case result cleaning limit (0 - no cleaning). */
    protected _cleanLimit: number = 0;
    /** Is case run blocking. */
    protected _blocking: boolean = true;
    /** Is case running in parallel. */
    protected _parallel: boolean = true;
    /** Amount of cores to run in parallel. */
    protected _cores: number = 4;
    /** Is case running in realtime. */
    protected _realtime: boolean = true;
    /** Case simulation end time. */
    protected _endTime: number = 1000;

    /**
     * Abstract method to add a new object
     * to a dictionary of phyngs. It must be
     * case type specific to account for various
     * types of phyngs.
     * @param {PhyngProps} props Phyng properties.
     * @protected
     */
    protected abstract addPhyngToDict(props: PhyngProps): void;

    /**
     * Abstract method to validate Physical Description
     * for Phyng creation. It must be case type specific
     * to account for various types of phyngs.
     * @param {PhysicalDescription} pd Physical Description of a phyng.
     * @protected
     */
    protected abstract validatePd(pd: PhysicalDescription): void;

    /**
     * Abstract method to update case phyngs
     * from a simulation server.
     */
    public abstract updatePhyngs(): void;

    constructor(host: string, wot: WoT.WoT, tm: any, name: string) {
        super(host, wot, tm);
        this._name = name;
        this.couplingUrl = `${this.host}/case/${this.name}`;
        this.phyngs = {};
        this.updateParams();
        this.updatePhyngs();
    }

    /**
     * Gets case name.
     * @return {string} name of a case.
     */
    public get name(): string {
        return this._name;
    }

    /**
     * Gets case type.
     * @return {string} type of a case.
     */
    public get type(): string {
        return this._type;
    }

    /**
     * Gets case mesh quality.
     * @return {number} case mesh quality.
     */
    public get meshQuality(): number {
        return this._meshQuality;
    }

    /**
     * Sets case mesh quality.
     * @param {number} meshQuality: mesh quality to set.
     * @async
     */
    public async setMeshQuality(meshQuality: number): Promise<void> {
        if (meshQuality > 0 && meshQuality <= 100) {
            this._meshQuality = meshQuality;
            await reqPatch(this.couplingUrl, {mesh_quality: meshQuality});
        } else {
            // TODO: error
            console.error(`Mesh quality should be in range 0..100, but ${meshQuality} was provided`)
        }
    }

    /**
     * Gets case cleaning limit.
     * @return {number} case cleaning limit.
     */
    public get cleanLimit(): number {
        return this._cleanLimit;
    }

    /**
     * Sets case result cleaning limit.
     * @param {number} cleanLimit: cleaning limit to set.
     * @async
     */
    public async setCleanLimit(cleanLimit: number): Promise<void> {
        if (cleanLimit < 0) {
            this._cleanLimit = cleanLimit;
            await reqPatch(this.couplingUrl, {clean_limit: cleanLimit});
        } else {
            // TODO: error
            console.error('Cleaning limit cannot be negative!')
        }
    }

    /**
     * Gets blocking flag.
     * @return {boolean} blocking flag.
     */
    public get blocking(): boolean {
        return this._blocking;
    }

    /**
     * Enable/disable case blocking solving.
     * @param {boolean} blocking: blocking flag.
     * @async
     */
    public async setBlocking(blocking: boolean): Promise<void> {
        this._blocking = blocking;
        await reqPatch(this.couplingUrl, {blocking});
    }

    /**
     * Gets parallel flag.
     * @return {boolean} parallel flag.
     */
    public get parallel(): boolean {
        return this._parallel;
    }

    /**
     * Enable/disable case parallel solving.
     * @param {boolean} parallel: parallel flag.
     * @async
     */
    public async setParallel(parallel: boolean): Promise<void> {
        this._parallel = parallel;
        await reqPatch(this.couplingUrl, {parallel});
    }

    /**
     * Gets number of cores for parallel run.
     * @return {number} number of cores.
     */
    public get cores(): number {
        return this._cores;
    }

    /**
     * Sets case number of cores for parallel run.
     * @param {number} cores: number of cores.
     * @async
     */
    public async setCores(cores: number): Promise<void> {
        if (cores < 0) {
            this._cores = cores;
            await reqPatch(this.couplingUrl, {cores});
        } else {
            console.log('Number of cores cannot be negative!')
        }
    }

    /**
     * Gets realtime flag.
     * @return {boolean} realtime flag.
     */
    public get realtime(): boolean {
        return this._realtime;
    }

    /**
     * Enable/disable case realtime solving.
     * @param {boolean} realtime: realtime flag.
     * @async
     */
    public async setRealtime(realtime: boolean): Promise<void> {
        this._realtime = realtime;
        await reqPatch(this.couplingUrl, {realtime});
    }

    /**
     * Gets simulation endtime.
     * @return {number} simulation endtime.
     */
    public get endTime(): number {
        return this._endTime;
    }

    /**
     * Sets simulation end time.
     * @param {number} endTime: simulation end-time.
     * @async
     */
    public async setEndTime(endTime: number): Promise<void> {
        this._endTime = endTime;
        await reqPatch(this.couplingUrl, {endtime: endTime});
    }

    /**
     * Runs a case.
     * @async
     */
    public async run(): Promise<void> {
        await this.executeCmd('run');
    }

    /**
     * Stops a case.
     * @async
     */
    public async stop(): Promise<void> {
        await this.executeCmd('stop');
    }

    /**
     * Setups a case.
     * @async
     */
    public async setup(): Promise<void> {
        await this.executeCmd('setup');
    }

    /**
     * Cleans a case.
     * @async
     */
    public async clean(): Promise<void> {
        await this.executeCmd('clean');
    }

    /**
     * Post processes a case.
     * @async
     */
    public async postprocess(data: any): Promise<void> {
        await this.executeCmd('postprocess', 'post', data);
    }

    /**
     * Returns the current time
     * parameters of a simulation.
     * @return {Promise<CaseTime>} Current time parameters of the simulation.
     */
    public async getTime(): Promise<CaseTime> {
        let data = await this.executeCmd('time', 'get');
        return {
            'real': data['real_time'],
            'simulation': data['simulation_time'],
            'difference': data['time_difference']
        };
    }

    /**
     * Updates case parameters from a simulation server.
     * @async
     */
    public async updateParams(): Promise<void> {
        let response = await reqGet(`${this.couplingUrl}`);
        let caseParams = response.data;
        this._meshQuality = caseParams.mesh_quality;
        this._cleanLimit = caseParams.clean_limit;
        this._parallel = caseParams.parallel;
        this._blocking = caseParams.blocking;
        this._cores = caseParams.cores;
    }

    /**
     * Adds Phyng with properties to simulation and instantiates a corresponding class.
     * @param {PhysicalDescription} pd Phyng properties.
     * @async
     */
    public async addPhyng(pd: PhysicalDescription): Promise<void> {
        this.validatePd(pd);
        let data: any = this.getDataFromPd(pd);
        let response = await reqPost(
            `${this.couplingUrl}/phyng/${pd.title}`,
            data
        );
        if (responseIsSuccessful(response.status)) {
            this.addPhyngToDictPd(pd);
        } else {
            throw Error(response.data);
        }
    }

    /**
     * Removes a Phyng with a given name from a simulator.
     * @param {string} name Name of a Phyng.
     */
    public async removePhyng(name: string): Promise<void> {
        if (!(name in this.phyngs)) return;
        await this.phyngs[name].destroy();
        delete this.phyngs[name];
    }

    /**
     * Gets case phyngs with their HREFs.
     * @return {PhyngHrefs[]} Phyngs with names, types and HREFs
     */
    public getPhyngs(): PhyngHrefs[] {
        let phyngs: PhyngHrefs[] = [];
        if (this.phyngs) {
            for (const name in this.phyngs) {
                phyngs.push({name, type: this.phyngs[name].type, hrefs: this.phyngs[name].getHrefs()});
            }
        }
        return phyngs;
    }

    /**
     * A funtion that should return a phyng type based on its TM 
     * Must be case specific
     * @param pd 
     */
    protected abstract findPhyngType(pd: PhysicalDescription): string

    /**
     * Gets Phyng data from PD
     * @param {PhysicalDescription} pd - Phyng Description
     * @protected
     */
    protected getDataFromPd(pd: PhysicalDescription): any {
        let data: any = {...pd.phyProperties, type: this.findPhyngType(pd)}
        if ('stlName' in pd.phyProperties) data['stl_name'] = pd.phyProperties.stlName;
        if ('dimensionsIn' in pd.phyProperties) data['dimensions_in'] = pd.phyProperties.dimensionsIn;
        if ('locationIn' in pd.phyProperties) data['location_in'] = pd.phyProperties.locationIn;
        if ('rotationIn' in pd.phyProperties) data['rotation_in'] = pd.phyProperties.rotationIn;
        if ('stlNameIn' in pd.phyProperties) data['stl_name_in'] = pd.phyProperties.stlNameIn;
        if ('dimensionsOut' in pd.phyProperties) data['dimensions_out'] = pd.phyProperties.dimensionsOut;
        if ('locationOut' in pd.phyProperties) data['location_out'] = pd.phyProperties.locationOut;
        if ('rotationOut' in pd.phyProperties) data['rotation_out'] = pd.phyProperties.rotationOut;
        if ('stlNameOut' in pd.phyProperties) data['stl_name_out'] = pd.phyProperties.stlNameOut;
        return data;
    }

    /**
     * Adds a new Phyng to a dictionary of phyngs via its PD.
     * @param {PhysicalDescription} pd Physical Description of a Phyng.
     * @protected
     */
    protected addPhyngToDictPd(pd: PhysicalDescription) {
        this.addPhyngToDict({...pd.phyProperties, name: pd.title, type: this.findPhyngType(pd)});
    }

    /**
     * Gets phyngs from a simulation.
     * @return {Promise<any>} Simulation phyngs.
     * @async
     * @protected
     */
    protected async getPhyngsFromSimulator(): Promise<any> {
        let response = await reqGet(`${this.couplingUrl}/phyng`);
        return response.data;
    }

    /**
     * Upload an ASCII STL file.
     * @param {any} data File form data.
     * @async
     * @protected
     */
    protected async uploadStl(data: any): Promise<void> {
        let formData = new FormData();
        let filename = data.match(/filename="(.*\.stl)"/)[1];
        let filePath = `${__dirname}/${filename}`;
        fs.writeFile(filePath, data.match(/(solid(.|\n)*endsolid\s.*)/gm)[0], () => {});
        formData.append('file', fs.createReadStream(filePath));
        await reqPost(`${this.couplingUrl}/uploadSTL`, formData,
            {
                headers: formData.getHeaders()
            });
        fs.unlinkSync(filePath)
    }

    /**
     * Executes a case command.
     * @param {CaseCommand} command Case command to execute.
     * @param {"get" | "post"} method Method to execute command with.
     * @async
     * @protected
     */
    protected async executeCmd(command: CaseCommand, method: 'get' | 'post' = 'post', data?: any): Promise<any> {
        if (method == 'post') console.log(data)
        let response: AxiosResponse = await makeRequest({method, url: `${this.couplingUrl}/${command}`, data});
        if (responseIsUnsuccessful(response.status)) {
            throw Error(response.data);
        }
        return response.data;
    }

    protected addPropertyHandlers(): void {
        this.thing.setPropertyReadHandler('meshQuality', async () => this.meshQuality);
        this.thing.setPropertyReadHandler('cleanLimit', async () => this.cleanLimit);
        this.thing.setPropertyReadHandler('blocking', async () => this.blocking);
        this.thing.setPropertyReadHandler('parallel', async () => this.parallel);
        this.thing.setPropertyReadHandler('cores', async () => this.cores);
        this.thing.setPropertyReadHandler('phyngs', async () => this.getPhyngs());
        this.thing.setPropertyReadHandler('time', async () => this.getTime());
        this.thing.setPropertyReadHandler('realtime', async () => this.realtime);
        this.thing.setPropertyReadHandler('endTime', async () => this.endTime);

        this.thing.setPropertyWriteHandler('meshQuality', async (meshQuality) => {
            await this.setMeshQuality(meshQuality);
        });
        this.thing.setPropertyWriteHandler('cleanLimit', async (cleanLimit) => {
            await this.setCleanLimit(cleanLimit);
        });
        this.thing.setPropertyWriteHandler('parallel', async (parallel) => {
            await this.setParallel(parallel);
        });
        this.thing.setPropertyWriteHandler('cores', async (cores) => {
            await this.setCores(cores);
        });
        this.thing.setPropertyWriteHandler('realtime', async (realtime) => {
            await this.setRealtime(realtime);
        });
        this.thing.setPropertyWriteHandler('endTime', async (endTime) => {
            await this.setEndTime(endTime);
        });
    }

    protected addActionHandlers(): void {
        this.thing.setActionHandler('run', async () => {
            await this.run();
        });
        this.thing.setActionHandler('stop', async () => {
            await this.stop();
        });
        this.thing.setActionHandler('setup', async () => {
            await this.setup();
        });
        this.thing.setActionHandler('clean', async () => {
            await this.clean();
        });
        this.thing.setActionHandler('postprocess', async (data: any) => {
            await this.postprocess(data);
        });
        this.thing.setActionHandler('addPhyng', async (pd: PhysicalDescription) => {
            await this.addPhyng(pd);
        });
        this.thing.setActionHandler('removePhyng', async (name) => {
            await this.removePhyng(name);
        });
        this.thing.setActionHandler('uploadSTL', async (data, options) => {
            await this.uploadStl(data);
        });
    }

    protected addEventHandlers(): void {
    }
}
