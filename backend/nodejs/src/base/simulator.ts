/**
 * Simulator module.
 *
 * @file   Contains a Simulator class that is used to wrap python simulations in node-wot interface along with helper interfaces.
 * @author Anatolii Tsirkunenko
 * @since  28.11.2021
 */
import {AbstractThing} from './thing';
import {AbstractCase} from './case';
import {CaseHrefs, SimulationErrors, CaseDescription} from './interfaces';
import {responseIsUnsuccessful, responseIsSuccessful} from './helpers';
import {reqGet, reqPost, reqPut, reqDelete} from './axios-requests';
import {AxiosResponse} from 'axios';
import {cdSchema, validateSchema} from './schemas';

/**
 * Case type constructor function.
 */
interface CaseTypeConstructor {
    (host: string, wot: WoT.WoT, tm: WoT.ThingDescription, name: string): AbstractCase;
}

/**
 * Case type constructor parameters.
 */
interface CaseTypeConstructorParams {
    /** Case type constructor. */
    constructor: CaseTypeConstructor;
    /** Case type thing model. */
    tm: WoT.ThingDescription;
    /** Case Description validator. */
    cdValidator: any;
}

/**
 * Case type constructor with type name as key.
 */
export interface CaseConstructorType {
    [type: string]: CaseTypeConstructorParams;
}

/**
 * Post-processing server parameters response.
 */
interface PostProcServerParamResp {
    hostname: string
    server_port: number
    multi_clients: boolean
    client_host: string
    connection_id: string
    cslog: string
    disable_further_connections: boolean
    disable_registry: boolean
    disable_xdisplay_test: boolean
    enable_bt: boolean
    enable_satellite_message_ids: boolean
    enable_streaming: boolean
    force_offscreen_rendering: boolean
    force_onscreen_rendering: boolean
    multi_clients_debug: boolean
    print_monitors: boolean
    reverse_connection: boolean
    test_plugin: string
    test_plugin_path: string
    test_dimensions_x: string
    test_dimensions_y: string
    tile_mullion_x: string
    tile_mullion_y: string
    timeout: string
    use_offscreen_rendering: string
}

/**
 * Post-processing server parameters interface.
 */
interface PostProcServerParam {
    /** Server hostname. */
    hostname: string
    /** Server port. */
    port: number
    /** Server support for multiple clients. */
    multiClients: boolean
}

/**
 * A simulator Thing. Provides a WoT wrapper to simulator backend.
 * @class Simulator
 */
export class Simulator extends AbstractThing {
    /** Cases used in a simulation. */
    protected cases: { [name: string]: AbstractCase };
    /** Array of cases used in a
     * simulation with their HREFs. */
    protected casesHrefs: CaseHrefs[];
    /** Case types constructors, used to
     * instantiate cases according to their type. */
    protected caseTypesConstructors: CaseConstructorType;
    /** Post-processing server parameters. */
    protected postProcServerParams: PostProcServerParam;

    constructor(host: string, wot: WoT.WoT, tm: WoT.ThingDescription, caseTypesConstructors: CaseConstructorType) {
        super(host, wot, tm);
        this.postProcServerParams = {
            hostname: 'localhost',
            port: 11111,
            multiClients: true
        }
        this.cases = {};
        this.casesHrefs = []
        this.couplingUrl = `${this.host}/case`
        this.caseTypesConstructors = caseTypesConstructors;
        this.loadAvailableCases();
        this.getPostProcServerParams();
    }

    /**
     * Constructs a case Thing according
     * to a type and assigns a name to it.
     * @param {string} type Type of a case.
     * @param {string} name Name of a new case.
     * @return {AbstractCase} A new case instance.
     * @protected
     */
    protected constructExposedCase(type: string, name: string): AbstractCase {
        let caseConstructorParams = this.caseTypesConstructors[type];
        caseConstructorParams.tm.title = name;
        return caseConstructorParams.constructor(this.host, this.wot, {...caseConstructorParams.tm}, name);
    };

    /**
     * Initializes a new case with a given name.
     * @param {string} name Name of a case to initialize.
     * @return {Promise<string | void>} Init error or nothing.
     * @protected
     * @async
     */
    protected async initCaseByName(name: string): Promise<string | void> {
        let response: AxiosResponse = await reqGet(`${this.couplingUrl}/${name}`);
        if (!(name in this.cases) && responseIsSuccessful(response.status)) {
            this.cases[name] = this.constructExposedCase(response.data.type, name);
            await this.cases[name].ready;
            this.casesHrefs.push({name, hrefs: this.cases[name].getHrefs()});
            return;
        }
        return response.data;
    }

    /**
     * Loads available cases from the simulator backend.
     * @return {Promise<string | void>} Load error or nothing.
     * @protected
     * @async
     */
    protected async loadAvailableCases(): Promise<string | void> {
        let response: AxiosResponse = await reqGet(`${this.couplingUrl}`);
        if (responseIsUnsuccessful(response.status)) {
            return response.data;
        }
        let caseNames: string[] = response.data;
        this.casesHrefs = [];
        for (const name of caseNames) {
            let normalName = `${name.replace('.case', '')}`;
            await this.initCaseByName(normalName);
        }
    }

    /**
     * Gets post-processing parameters.
     * @return {Promise<string | void>} Get error or nothing.
     * @protected
     * @async
     */
    protected async getPostProcServerParams(): Promise<string | void> {
        let response: AxiosResponse = await reqGet(`${this.host}/postprocess`);
        if (responseIsUnsuccessful(response.status)) {
            return response.data;
        }
        let data: PostProcServerParamResp = response.data;
        this.postProcServerParams = {
            hostname: data.hostname,
            port: data.server_port,
            multiClients: data.multi_clients,
        }
    }

    /**
     * Updates post-processing parameters.
     * @return {Promise<string | void>} Update error or nothing.
     * @protected
     * @async
     */
    protected async updatePostProcServerParams(postProcServerParams: PostProcServerParam): Promise<string | void> {
        this.postProcServerParams.hostname = postProcServerParams.hostname || this.postProcServerParams.hostname;
        this.postProcServerParams.port = postProcServerParams.port || this.postProcServerParams.port;
        this.postProcServerParams.multiClients = postProcServerParams.multiClients || this.postProcServerParams.multiClients;
        // this.postProcServerParams = postProcServerParams;
        console.log(postProcServerParams)
        let response: AxiosResponse = await reqPut(`${this.host}/postprocess`, postProcServerParams);
        if (responseIsUnsuccessful(response.status)) {
            return response.data;
        }
    }

    /**
     * Starts post-processing server.
     * @return {Promise<string | void>} Server start error or nothing.
     * @protected
     * @async
     */
    protected async startPostProcessingServer(): Promise<string | void> {
        let response: AxiosResponse = await reqPost(`${this.host}/postprocess/start`);
        if (responseIsUnsuccessful(response.status)) {
            return response.data;
        }
    }

    /**
     * Stops post-processing server.
     * @return {Promise<string | void>} Server stop error or nothing.
     * @protected
     * @async
     */
    protected async stopPostProcessingServer(): Promise<string | void> {
        let response: AxiosResponse = await reqPost(`${this.host}/postprocess/stop`);
        if (responseIsUnsuccessful(response.status)) {
            return response.data;
        }
    }

    /**
     * Returns simulation errors object.
     * @return {Promise<SimulationErrors>} Simulator errors object.
     * @async
     */
    public async getErrors(): Promise<SimulationErrors> {
        let response: AxiosResponse = await reqGet(`${this.host}/errors`);
        return response.data;
    }

    /**
     * Finds case type based on link
     * @param cd cd Case Description of a case.
     * @returns 
     */
    public findCaseType(cd: CaseDescription) {
        let typeLink = '';
        let type= '';
        const links = cd.links
        for(let link of links) {
            if('rel' in link && link.rel === 'type') typeLink = link.href.toLowerCase()
            if(typeLink.includes('cht')) type = 'cht'
        }
        return type
    }

    /**
     * Creates case with given parameters on the simulator backend.
     * @param {CaseDescription} cd Case Description of a case.
     * @return {Promise<string>} Simulator backend response promise.
     * @async
     */
    public async createCase(cd: CaseDescription): Promise<string> {
        this.validateCd(cd);
        let data: any = {...cd.sysProperties, type: this.findCaseType(cd)}
        if (cd.sysProperties.meshQuality) data['mesh_quality'] = cd.sysProperties.meshQuality;
        if (cd.sysProperties.cleanLimit) data['clean_limit'] = cd.sysProperties.cleanLimit;
        if (cd.sysProperties.endTime) data['end_time'] = cd.sysProperties.endTime;
        let response: AxiosResponse = await reqPost(`${this.couplingUrl}/${cd.title}`, data);
        await this.initCaseByName(cd.title);
        return response.data;
    }

    /**
     * Deletes case by its name.
     * @param {string} name Name of the case.
     * @return {Promise<string>} Simulator backend response promise.
     * @async
     */
    public async deleteCase(name: string): Promise<string> {
        if (name in this.cases) {
            let index = this.casesHrefs.findIndex(x => x.name === name);
            this.casesHrefs.splice(index, 1);
            await this.cases[name].destroy();
            delete this.cases[name];
        }
        let response: AxiosResponse = await reqDelete(`${this.couplingUrl}/${name}`);
        return response.data;
    }

    /**
     * Validates given Case Description.
     * @param {CaseDescription} cd Case Description of a case.
     */
    protected validateCd(cd: CaseDescription): void {
        validateSchema(cd, cdSchema);
        validateSchema(cd, this.caseTypesConstructors[this.findCaseType(cd)].cdValidator);
    }

    protected addPropertyHandlers(): void {
        this.thing.setPropertyReadHandler('cases', async () => {
            return this.casesHrefs;
        });
        this.thing.setPropertyReadHandler('errors', async () => {
            return await this.getErrors();
        });
        this.thing.setPropertyReadHandler('postProcessingServer', async () => {
            return this.postProcServerParams;
        });
        this.thing.setPropertyWriteHandler('postProcessingServer',
            async (postProcServerParams: PostProcServerParam) => {
                return await this.updatePostProcServerParams(postProcServerParams);
            });
    }

    protected addActionHandlers(): void {
        this.thing.setActionHandler('createCase', async (sd: CaseDescription) => {
            return await this.createCase(sd);
        });
        this.thing.setActionHandler('deleteCase', async (name: string) => {
            return await this.deleteCase(name);
        });
        this.thing.setActionHandler('startPostProcessingServer', async () => {
            return await this.startPostProcessingServer();
        });
        this.thing.setActionHandler('stopPostProcessingServer', async () => {
            return await this.stopPostProcessingServer();
        });
    }

    protected addEventHandlers(): void {
    }
}
