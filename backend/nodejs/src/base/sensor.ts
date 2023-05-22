/**
 * Sensor Phyng module.
 *
 * @file   Contains a Sensor abstract class and other sensor types based on it.
 * @author Anatolii Tsirkunenko
 * @since  29.11.2021
 */
import {AbstractPhyng} from './phyng';
import {SensorProps} from './interfaces';
import {responseIsUnsuccessful} from "./helpers";
import {reqGet} from './axios-requests';

/** Sensors common TM. */
const sensorTm: WoT.ThingDescription = require('../../tms/base/baseSensor.model.json');

/**
 * An abstract Sensor Phyng class.
 *
 * Abstract class used by sensor node-things in this application.
 * @class Sensor
 * @abstract
 */
export abstract class Sensor extends AbstractPhyng implements SensorProps {
    /** Sensor field to monitor, e.g., "T". */
    protected _field: string;

    protected constructor(host: string, wot: WoT.WoT, tm: any, caseName: string, props: SensorProps) {
        super(host, wot, tm, caseName, props);
        this._field = props.field;
    }

    /**
     * Gets sensor Phyng field.
     * @return {string} field of a sensor Phyng.
     */
    public get field() {
        return this._field;
    }

    /**
     * Gets value of a sensor Phyng.
     * @return {Promise<any>} Value of a sensor Phyng.
     * @async
     * @protected
     */
    protected async getValue(): Promise<any> {
        let response = await reqGet(`${this.couplingUrl}/value`);
        if (responseIsUnsuccessful(response.status)) {
            console.error(response.data);
        }
        return response.data;
    }
}

/**
 * Temperature Sensor class.
 *
 * Generic temperature sensor Phyng.
 * @class TemperatureSensor
 */
export class TemperatureSensor extends Sensor {
    constructor(host: string, wot: WoT.WoT, caseName: string, props: SensorProps) {
        let tm: WoT.ThingDescription = {...sensorTm}; // Default TM
        tm.properties.temperature = {...tm.properties.value};
        tm.properties.temperature.type = 'number';
        tm.properties.temperature.units = 'K';
        delete tm.properties.value;
        super(host, wot, tm, caseName, props);
    }

    protected addPropertyHandlers() {
        this.thing.setPropertyReadHandler('temperature', async () =>
            await this.getValue()
        );
    }

    protected addActionHandlers() {
    }

    protected addEventHandlers() {
    }
}

/**
 * Sensor creator function.
 *
 * Returns a new instance of a sensor according to its type.
 * @param {string} host IP address of a simulation server.
 * @param {WoT} wot Web of Things interface.
 * @param {caseName} caseName Name of the case an object is assigned to.
 * @param {SensorProps} props Sensor properties.
 * @return {Sensor | undefined} New Sensor instance or undefined.
 */
export function newSensor(host: string, wot: WoT.WoT, caseName: string, props: SensorProps): Sensor | undefined {
    switch (props.field) {
        case 'T':
            return new TemperatureSensor(host, wot, caseName, props);
        default:
            console.error(`Field ${props.field} for sensor ${props.name} is not implemented`);
            break;
    }
}
