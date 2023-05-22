/**
 * Actuator Phyng module.
 *
 * @file   Contains an Actuator class that is used by actuator node-things in this application.
 * @author Anatolii Tsirkunenko
 * @since  29.11.2021
 */
import {AbstractPhyng} from './phyng';
import {ActuatorPropsCreated, ActuatorPropsStl, Size, Vector} from './interfaces';
import {responseIsUnsuccessful} from "./helpers";
import {reqPatch} from './axios-requests';

/**
 * An abstract actuator Phyng.
 *
 * Abstract class used by actuator node-things in this application.
 * @class Actuator
 * @abstract
 */
export abstract class Actuator extends AbstractPhyng implements ActuatorPropsCreated, ActuatorPropsStl {
    /** Actuator dimensions. */
    protected _dimensions: Size;
    /** Actuator rotation. */
    protected _rotation: Vector;
    /** Actuator geometry STL name. */
    protected _stlName: string;

    protected constructor(host: string, wot: WoT.WoT, tm: any, caseName: string,
                          props: ActuatorPropsCreated | ActuatorPropsStl) {
        super(host, wot, tm, caseName, props);
        this._rotation = 'rotation' in props && props.rotation ? props.rotation : [0, 0, 0];
        this._dimensions = 'dimensions' in props ? props.dimensions : [0, 0, 0];
        this._stlName = 'stlName' in props ? props.stlName : '';
    }

    /**
     * Gets actuator Phyng dimensions
     * @return {Size} dimensions of an actuator Phyng.
     */
    public get dimensions(): Size {
        return this._dimensions;
    }

    /**
     * Sets actuator dimensions.
     * @param {Size} dimensions: dimensions to set.
     * @async
     */
    public async setDimensions(dimensions: Size): Promise<void> {
        this._dimensions = dimensions;
        let response = await reqPatch(`${this.couplingUrl}`, { dimensions });
        if (responseIsUnsuccessful(response.status)) {
            console.error(response.data);
        }
    }

    /**
     * Gets actuator Phyng rotation
     * @return {Vector} rotation of an actuator Phyng.
     */
    public get rotation(): Vector {
        return this._rotation;
    }

    /**
     * Sets actuator rotation.
     * @param {Vector} rotation: rotation to set.
     * @async
     */
    public async setRotation(rotation: Vector): Promise<void> {
        this._rotation = rotation;
        let response = await reqPatch(`${this.couplingUrl}`, { rotation });
        if (responseIsUnsuccessful(response.status)) {
            console.error(response.data);
        }
    }

    /**
     * Gets actuator Phyng geometry STL name.
     * @return {string} template name of an actuator Phyng.
     */
    public get stlName(): string {
        return this._stlName;
    }

    /**
     * Sets actuator geometry STL name.
     * @param {string} stlName: template to set.
     * @async
     */
    public async setStlName(stlName: string): Promise<void> {
        this._stlName = stlName;
        let response = await reqPatch(`${this.couplingUrl}`, { stl_name: stlName });
        if (responseIsUnsuccessful(response.status)) {
            console.error(response.data);
        }
    }

    protected addPropertyHandlers(): void {
        super.addPropertyHandlers();
        this.thing.setPropertyReadHandler('dimensions', async () => this.dimensions);
        this.thing.setPropertyWriteHandler('dimensions', async (dimensions) =>
            await this.setDimensions(dimensions)
        );
        this.thing.setPropertyReadHandler('rotation', async () => this.rotation);
        this.thing.setPropertyWriteHandler('rotation', async (rotation) =>
            await this.setRotation(rotation)
        );
        this.thing.setPropertyReadHandler('stlName', async () => this.stlName);
        this.thing.setPropertyWriteHandler('stlName', async (stlName) =>
            await this.setStlName(stlName)
        );
    }

    protected addActionHandlers(): void {
    }

    protected addEventHandlers(): void {
    }
}
