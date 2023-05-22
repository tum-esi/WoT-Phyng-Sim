/**
 * Conjugate Heat Transfer (CHT) behavior module.
 *
 * @file   Contains phyngs associated with CHT case and the case itself.
 * @author Anatolii Tsirkunenko
 * @since  01.12.2021
 */
import {use} from 'typescript-mix';
import {
    EnableableProperties,
    HeatingProperties,
    OpenableProperties,
    RotatableProperties,
    VelocityProperties
} from '../base/properties'
import {Actuator} from '../base/actuator';
import {
    ActuatorProps,
    Coordinates,
    PhyngProps,
    PhysicalDescription,
    SensorProps,
    Size,
    Vector
} from '../base/interfaces';
import {newSensor} from '../base/sensor';
import {AbstractCase} from '../base/case';
import {reqPatch} from '../base/axios-requests';
import {chtPdSchema, validateSchema} from '../base/schemas';
import {responseIsUnsuccessful} from "../base/helpers";

/** Walls common TM. */
let wallsTm = require('../../tms/behavior/cht/chtWalls.model.json');
/** Heater common TM. */
let heaterTm = require('../../tms/behavior/cht/chtHeater.model.json');
/** Window common TM. */
let windowTm = require('../../tms/behavior/cht/chtWindow.model.json');
/** Door common TM. */
let doorTm = require('../../tms/behavior/cht/chtDoor.model.json');
/** AC common TM. */
let acTm = require('../../tms/behavior/cht/chtAc.model.json');

/** Heater interface wrapper for
 * multiple class extension. */
interface Heater extends HeatingProperties {
}

/**
 * CHT heater Phyng class.
 *
 * Heater Phyng that is used in CHT case.
 * @class Heater
 */
class Heater extends Actuator {
    @use(HeatingProperties) this: any;

    constructor(host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) {
        let tm = {...heaterTm}; // Default TM
        super(host, wot, tm, caseName, props);
    }

    protected addPropertyHandlers() {
        super.addPropertyHandlers();
        this.setTemperatureGetHandler(this.thing, this.couplingUrl);
        this.setTemperatureSetHandler(this.thing, this.couplingUrl);
    }

    protected addActionHandlers() {
        super.addActionHandlers();
    }

    protected addEventHandlers() {
    }
}

/** Walls interface wrapper for
 * multiple class extension. */
interface Walls extends HeatingProperties {
}

/**
 * CHT walls Phyng class.
 *
 * Walls Phyng that is used in CHT case.
 * @class Walls
 */
class Walls extends Actuator {
    @use(HeatingProperties) this: any;

    constructor(host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) {
        let tm = {...wallsTm}; // Default TM
        super(host, wot, tm, caseName, props);
    }

    protected addPropertyHandlers() {
        super.addPropertyHandlers();
        this.setTemperatureGetHandler(this.thing, this.couplingUrl);
        this.setTemperatureSetHandler(this.thing, this.couplingUrl);
    }

    protected addActionHandlers() {
        super.addActionHandlers();
    }

    protected addEventHandlers() {
    }
}

/** Door interface wrapper for
 * multiple class extension. */
interface Door extends HeatingProperties, VelocityProperties, OpenableProperties {
}

/**
 * CHT door Phyng class.
 *
 * Door Phyng that is used in CHT case.
 * @class Door
 */
class Door extends Actuator {
    @use(HeatingProperties, VelocityProperties, OpenableProperties) this: any;

    constructor(host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) {
        let tm = {...doorTm}; // Default TM
        super(host, wot, tm, caseName, props);
    }

    protected addPropertyHandlers() {
        super.addPropertyHandlers();
        this.setTemperatureGetHandler(this.thing, this.couplingUrl);
        this.setTemperatureSetHandler(this.thing, this.couplingUrl);
        this.setVelocityGetHandler(this.thing, this.couplingUrl);
        this.setVelocitySetHandler(this.thing, this.couplingUrl);
        this.setOpenedGetHandler(this.thing, this.couplingUrl);
    }

    protected addActionHandlers() {
        super.addActionHandlers();
        this.setOpenSetHandler(this.thing, this.couplingUrl);
        this.setCloseSetHandler(this.thing, this.couplingUrl);
    }

    protected addEventHandlers() {
    }
}

/** Window interface wrapper for
 * multiple class extension. */
interface Window extends HeatingProperties, VelocityProperties, OpenableProperties {
}

/**
 * CHT window Phyng class.
 *
 * Window Phyng that is used in CHT case.
 * @class Window
 */
class Window extends Actuator {
    @use(HeatingProperties, VelocityProperties, OpenableProperties) this: any;

    constructor(host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) {
        let tm = {...windowTm}; // Default TM
        super(host, wot, tm, caseName, props);
    }

    protected addPropertyHandlers() {
        super.addPropertyHandlers();
        this.setTemperatureGetHandler(this.thing, this.couplingUrl);
        this.setTemperatureSetHandler(this.thing, this.couplingUrl);
        this.setVelocityGetHandler(this.thing, this.couplingUrl);
        this.setVelocitySetHandler(this.thing, this.couplingUrl);
        this.setOpenedGetHandler(this.thing, this.couplingUrl);
    }

    protected addActionHandlers() {
        super.addActionHandlers();
        this.setOpenSetHandler(this.thing, this.couplingUrl);
        this.setCloseSetHandler(this.thing, this.couplingUrl);
    }

    protected addEventHandlers() {
    }
}

/** AC interface wrapper for
 * multiple class extension. */
interface AC extends HeatingProperties, VelocityProperties, RotatableProperties, EnableableProperties {
}

/**
 * CHT AC Phyng class.
 *
 * AC Phyng that is used in CHT case.
 * @class AC
 */
class AC extends Actuator {
    @use(HeatingProperties, VelocityProperties, RotatableProperties, EnableableProperties) this: any;
    /** AC inlet location. */
    protected _locationIn: Coordinates;
    /** AC outlet location. */
    protected _locationOut: Coordinates;
    /** AC inlet dimensions. */
    protected _dimensionsIn: Coordinates;
    /** AC outlet dimensions. */
    protected _dimensionsOut: Coordinates;
    /** AC inlet rotation. */
    protected _rotationIn: Size;
    /** AC outlet rotation. */
    protected _rotationOut: Size;
    /** AC inlet geometry STL name. */
    protected _stlNameIn: string;
    /** AC outlet geometry STL name. */
    protected _stlNameOut: string;

    constructor(host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) {
        let tm = {...acTm}; // Default TM
        super(host, wot, tm, caseName, props);
        this._locationIn = 'locationIn' in props && props.locationIn ? props.locationIn : [0, 0, 0];
        this._locationOut = 'locationOut' in props && props.locationOut ? props.locationOut : [0, 0, 0];
        this._rotationIn = 'rotationIn' in props && props.rotationIn ? props.rotationIn : [0, 0, 0];
        this._rotationOut = 'rotationOut' in props && props.rotationOut ? props.rotationOut : [0, 0, 0];
        this._dimensionsIn = 'dimensionsIn' in props ? props.dimensionsIn! : [0, 0, 0];
        this._dimensionsOut = 'dimensionsOut' in props ? props.dimensionsOut! : [0, 0, 0];
        this._stlNameIn = 'stlNameIn' in props ? props.stlNameIn! : '';
        this._stlNameOut = 'stlNameOut' in props ? props.stlNameOut! : '';
    }

    /**
     * Gets AC inlet location
     * @return {Coordinates} location of a Phyng's inlet
     */
    public get locationIn(): Coordinates {
        return this._locationIn;
    }

    /**
     * Sets Phyng inlet location.
     * @param {Coordinates} location: inlet location to set.
     * @async
     */
    public async setLocationIn(location: Coordinates): Promise<void> {
        this._locationIn = location;
        let response = await reqPatch(`${this.couplingUrl}`, { location_in: location });
        if (responseIsUnsuccessful(response.status)) {
            throw Error(response.data);
        }
    }

    /**
     * Gets AC outlet location
     * @return {Coordinates} location of a Phyng's outlet
     */
    public get locationOut(): Coordinates {
        return this._locationOut;
    }

    /**
     * Sets Phyng outlet location.
     * @param {Coordinates} location: outlet location to set.
     * @async
     */
    public async setLocationOut(location: Coordinates): Promise<void> {
        this._locationOut = location;
        let response = await reqPatch(`${this.couplingUrl}`, { location_out: location });
        if (responseIsUnsuccessful(response.status)) {
            throw Error(response.data);
        }
    }

    /**
     * Gets AC inlet dimensions
     * @return {Size} dimensions of an AC inlet.
     */
    public get dimensionsIn(): Size {
        return this._dimensionsIn;
    }

    /**
     * Sets AC inlet dimensions.
     * @param {Size} dimensionsIn: inlet dimensions to set.
     * @async
     */
    public async setDimensionsIn(dimensionsIn: Size): Promise<void> {
        this._dimensionsIn = dimensionsIn;
        let response = await reqPatch(`${this.couplingUrl}`, { dimensions_in: dimensionsIn });
        if (responseIsUnsuccessful(response.status)) {
            console.error(response.data);
        }
    }

    /**
     * Gets AC outlet dimensions
     * @return {Size} dimensions of an AC outlet.
     */
    public get dimensionsOut(): Size {
        return this._dimensionsOut;
    }

    /**
     * Sets AC outlet dimensions.
     * @param {Size} dimensionsOut: outlet dimensions to set.
     * @async
     */
    public async setDimensionsOut(dimensionsOut: Size): Promise<void> {
        this._dimensionsOut = dimensionsOut;
        let response = await reqPatch(`${this.couplingUrl}`, { dimensionsout: dimensionsOut });
        if (responseIsUnsuccessful(response.status)) {
            console.error(response.data);
        }
    }

    /**
     * Gets AC inlet rotation
     * @return {Vector} rotation of an AC inlet.
     */
    public get rotationIn(): Vector {
        return this._rotationIn;
    }

    /**
     * Sets aC inlet rotation.
     * @param {Vector} rotationIn: inlet rotation to set.
     * @async
     */
    public async setRotationIn(rotationIn: Vector): Promise<void> {
        this._rotationIn = rotationIn;
        let response = await reqPatch(`${this.couplingUrl}`, { rotation_in: rotationIn });
        if (responseIsUnsuccessful(response.status)) {
            console.error(response.data);
        }
    }

    /**
     * Gets AC out rotation
     * @return {Vector} rotation of an AC out.
     */
    public get rotationOut(): Vector {
        return this._rotationOut;
    }

    /**
     * Sets aC out rotation.
     * @param {Vector} rotationOut: out rotation to set.
     * @async
     */
    public async setRotationOut(rotationOut: Vector): Promise<void> {
        this._rotationOut = rotationOut;
        let response = await reqPatch(`${this.couplingUrl}`, { rotation_out: rotationOut });
        if (responseIsUnsuccessful(response.status)) {
            console.error(response.data);
        }
    }

    /**
     * Gets AC inlet geometry STL name.
     * @return {string} inlet STL name of an AC inlet.
     */
    public get stlNameIn(): string {
        return this._stlNameIn;
    }

    /**
     * Sets AC inlet geometry STL name.
     * @param {string} stlNameIn: inlet STL name to set.
     * @async
     */
    public async setStlNameIn(stlNameIn: string): Promise<void> {
        this._stlNameIn = stlNameIn;
        let response = await reqPatch(`${this.couplingUrl}`, { stl_name_in: stlNameIn });
        if (responseIsUnsuccessful(response.status)) {
            console.error(response.data);
        }
    }

    /**
     * Gets AC out geometry STL name.
     * @return {string} outlet STL name of an AC out.
     */
    public get stlNameOut(): string {
        return this._stlNameOut;
    }

    /**
     * Sets AC out geometry STL name.
     * @param {string} stlNameOut: outlet STL name to set.
     * @async
     */
    public async setStlNameOut(stlNameOut: string): Promise<void> {
        this._stlNameOut = stlNameOut;
        let response = await reqPatch(`${this.couplingUrl}`, { stl_name_out: stlNameOut });
        if (responseIsUnsuccessful(response.status)) {
            console.error(response.data);
        }
    }

    protected addPropertyHandlers() {
        super.addPropertyHandlers();
        this.thing.setPropertyReadHandler('dimensionsIn', async () => this.dimensionsIn);
        this.thing.setPropertyWriteHandler('dimensionsIn', async (dimensionsIn) =>
            await this.setDimensionsIn(dimensionsIn)
        );
        this.thing.setPropertyReadHandler('dimensionsOut', async () => this.dimensionsOut);
        this.thing.setPropertyWriteHandler('dimensionsOut', async (dimensionsOut) =>
            await this.setDimensionsOut(dimensionsOut)
        );
        this.thing.setPropertyReadHandler('rotationIn', async () => this.rotationIn);
        this.thing.setPropertyWriteHandler('rotationIn', async (rotationIn) =>
            await this.setRotationIn(rotationIn)
        );
        this.thing.setPropertyReadHandler('rotationOut', async () => this.rotationOut);
        this.thing.setPropertyWriteHandler('rotationOut', async (rotationOut) =>
            await this.setRotationOut(rotationOut)
        );
        this.thing.setPropertyReadHandler('stlNameIn', async () => this.stlNameIn);
        this.thing.setPropertyWriteHandler('stlNameIn', async (stlNameIn) =>
            await this.setStlNameIn(stlNameIn)
        );
        this.thing.setPropertyReadHandler('stlNameOut', async () => this.stlNameOut);
        this.thing.setPropertyWriteHandler('stlNameOut', async (stlNameOut) =>
            await this.setStlNameOut(stlNameOut)
        );
        this.setTemperatureGetHandler(this.thing, this.couplingUrl);
        this.setTemperatureSetHandler(this.thing, this.couplingUrl);
        this.setVelocityGetHandler(this.thing, this.couplingUrl);
        this.setVelocitySetHandler(this.thing, this.couplingUrl);
        this.setAngleGetHandler(this.thing, this.couplingUrl);
        this.setAngleSetHandler(this.thing, this.couplingUrl);
        this.setEnabledGetHandler(this.thing, this.couplingUrl);
    }

    protected addActionHandlers() {
        super.addActionHandlers();
        this.setTurnOffHandler(this.thing, this.couplingUrl);
        this.setTurnOnHandler(this.thing, this.couplingUrl);
    }

    protected addEventHandlers() {
    }
}

/**
 * CHT object constructors for various
 * types of phyngs used in CHT case
 */
const chtObjectConstructors: { [type: string]: Function } = {
    heater: (host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) => new Heater(host, wot, caseName, props),
    walls: (host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) => new Walls(host, wot, caseName, props),
    window: (host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) => new Window(host, wot, caseName, props),
    door: (host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) => new Door(host, wot, caseName, props),
    ac: (host: string, wot: WoT.WoT, caseName: string, props: ActuatorProps) => new AC(host, wot, caseName, props),
    sensor: (host: string, wot: WoT.WoT, caseName: string, props: SensorProps) => newSensor(host, wot, caseName, props)
};

/**
 * Conjugate Heat Transfer (CHT) case class.
 * @class ChtCase
 */
export class ChtCase extends AbstractCase {
    /** Background region material. */
    protected _background: string = 'air';


    protected findPhyngType(pd: PhysicalDescription) {
        let typeLink = '';
        let type= '';
        const links = pd.links
        for(let link of links) {
            if('rel' in link && link.rel === 'type') typeLink = link.href.toLowerCase()

            if(typeLink.includes('wall')) type = 'walls'
            if(typeLink.includes('window')) type = 'window'
            if(typeLink.includes('door')) type = 'door'
            if(typeLink.includes('heater')) type = 'heater'
            if(typeLink.includes('ac')) type = 'ac'
            if(typeLink.includes('sensor')) type = 'sensor'
        }
        return type
    }

    /**
     * Gets background region material name.
     * @return {string} Background region material name.
     */
    public get background(): string {
        return this._background;
    }

    /**
     * Sets background region material name.
     * @param {string} background Background region material name to set.
     * @async
     */
    public async setBackground(background: string): Promise<void> {
        this._background = background;
        let response = await reqPatch(this.couplingUrl, {background});
        if (response.status / 100 !== 2) {
            console.error(response.data);
        }
    }

    /**
     * Updates CHT case phyngs from a simulation server.
     */
    public async updatePhyngs() {
        let objects = await this.getPhyngsFromSimulator();
        if (objects) {
            for (const object of objects) {
                this.addPhyngToDict(object);
            }
        }
    }

    /**
     * Validates Physical Description for CHT object creation.
     * @param {PhysicalDescription} pd Physical Description of an object.
     * @protected
     */
    protected validatePd(pd: PhysicalDescription): void {
        validateSchema(pd, chtPdSchema);
    }

    /**
     * Adds a new object to a dictionary of phyngs.
     * @param {PhyngProps} props Object properties.
     * @protected
     */
    protected addPhyngToDict(props: PhyngProps) {
        let objectConstructor = chtObjectConstructors[props.type];
        this.phyngs[props.name] = objectConstructor(this.host, this.wot, this.name, props);
    }

    protected addPropertyHandlers() {
        super.addPropertyHandlers();
        this.thing.setPropertyReadHandler('background', async () => this.background);
        this.thing.setPropertyWriteHandler('background', async (background) => {
            await this.setBackground(background);
        });
    }
}
