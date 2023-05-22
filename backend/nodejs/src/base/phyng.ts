/**
 * Phyng module.
 *
 * @file   Contains an AbstractPhyng class that is used by simulated Phyngs in this application.
 * @author Anatolii Tsirkunenko
 * @since  29.11.2021
 */
import {AbstractThing} from './thing';
import {Coordinates, PhyngProps} from './interfaces';
import {responseIsUnsuccessful} from './helpers';
import {reqGet, reqPatch, reqDelete} from './axios-requests';

/**
 * An abstract Phyng.
 *
 * Abstract class used by simulated Phyngs things in this application.
 * @class AbstractPhyng
 * @abstract
 */
export abstract class AbstractPhyng extends AbstractThing {
    /** Name of the case an phyng is assigned to. */
    protected caseName: string;
    /** Phyng location. */
    protected _location: Coordinates;
    /** Phyng name. */
    public _name: string;
    /** Phyng type, e.g., "sensor", "heater", etc. */
    protected _type: string;

    protected constructor(host: string, wot: WoT.WoT, tm: any, caseName: string, props: PhyngProps) {
        // Base URL cannot be yet set in node-wot,
        // thus a case name is added to a things model title
        tm.title = `${caseName}-${props.name}`
        super(host, wot, tm);
        this._name = props.name;
        this._type = props.type;
        this._location = 'location' in props && props.location ? props.location : [0, 0, 0];
        this.caseName = caseName;
        this.couplingUrl = `${this.host}/case/${this.caseName}/phyng/${this._name}`;
    }

    /**
     * Gets Phyng name
     * @return {string} name of a Phyng
     */
    public get name(): string {
        return this._name;
    }

    /**
     * Gets Phyng type
     * @return {string} type of a Phyng
     */
    public get type(): string {
        return this._type;
    }

    /**
     * Gets Phyng location
     * @return {Coordinates} location of a Phyng
     */
    public get location(): Coordinates {
        return this._location;
    }

    /**
     * Sets Phyng location.
     * @param {Coordinates} location: location to set.
     * @async
     */
    public async setLocation(location: Coordinates): Promise<void> {
        this._location = location;
        let response = await reqPatch(`${this.couplingUrl}`, { location });
        if (responseIsUnsuccessful(response.status)) {
            throw Error(response.data);
        }
    }

    /**
     * Gets Phyng parameters from a simulation server.
     * @return {Promise<any>} Phyng parameters from simulator.
     * @async
     */
    protected async getParamsFromSimulation(): Promise<any> {
        let response = await reqGet(`${this.couplingUrl}`);
        if (this._name in response.data) {
            return response.data[this._name];
        }
        return {};
    }

    /**
     * Updates Phyng parameters from a simulation server.
     * @async
     */
    public async updateParams(): Promise<void> {
        let phyngParams = await this.getParamsFromSimulation();
        this._location = phyngParams.location;
    }

    public async destroy(): Promise<void> {
        let response = await reqDelete(this.couplingUrl);
        if (responseIsUnsuccessful(response.status)) {
            throw Error(response.data);
        }
        await super.destroy();
    }

    protected addPropertyHandlers(): void {
        this.thing.setPropertyReadHandler('type', async () => this.type);
        this.thing.setPropertyReadHandler('location', async () => this.location);
        this.thing.setPropertyWriteHandler('location', async (location) =>
            await this.setLocation(location)
        );
    }
}
