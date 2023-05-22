/**
 * Properties module.
 *
 * @file   Contains various Property classes used to define actuator interaction affordances.
 * @author Anatolii Tsirkunenko
 * @since  01.11.2021
 */
import {AnyUri} from 'wot-thing-description-types';
import {Vector} from './interfaces';
import {reqGet, reqPost} from './axios-requests';
import {responseIsUnsuccessful} from "./helpers";

async function phyngValueSetter(url: string, value: any) {
    value = JSON.stringify(value);
    let response = await reqPost(url, {value});
    if (responseIsUnsuccessful(response.status)) {
        throw Error(response.data);
    }
    return response.data;
}

/**
 * Actuator heating properties.
 *
 * This class can be extended by an Actuator class to inherit heating properties.
 * @class HeatingProperties
 */
export class HeatingProperties {
    /**
     * Get temperature of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @return {Promise<number>} Temperature of an actuator.
     */
    public async getTemperature(couplingUrl: AnyUri): Promise<number> {
        let response = await reqGet(`${couplingUrl}/temperature`);
        return response.data;
    }

    /**
     * Set temperature of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @param {number} temperature Temperature to set on an actuator.
     * @return {Promise<any>} Server response.
     */
    public async setTemperature(couplingUrl: AnyUri, temperature: number): Promise<any> {
        return await phyngValueSetter(`${couplingUrl}/temperature`, temperature);
    }

    /**
     * Sets Web of Things temperature get handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setTemperatureGetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyReadHandler('temperature', async () =>
            await this.getTemperature(couplingUrl)
        );
    }

    /**
     * Sets Web of Things temperature set handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setTemperatureSetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyWriteHandler('temperature', async (temperature) =>
            await this.setTemperature(couplingUrl, temperature)
        );
    }
}

/**
 * Actuator fluid velocity properties.
 *
 * This class can be extended by an Actuator class to inherit fluid velocity properties.
 * @class HeatingProperties
 */
export class VelocityProperties {
    /**
     * Get fluid velocity of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @return {Promise<Vector>} Fluid velocity of an actuator.
     */
    public async getVelocity(couplingUrl: AnyUri): Promise<Vector> {
        let response = await reqGet(`${couplingUrl}/velocity`);
        return response.data;
    }

    /**
     * Set fluid velocity of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @param {Vector} velocity Fluid velocity to set on an actuator.
     * @return {Promise<any>} Server response.
     */
    public async setVelocity(couplingUrl: AnyUri, velocity: Vector): Promise<any> {
        return await phyngValueSetter(`${couplingUrl}/velocity`, velocity);
    }

    /**
     * Sets Web of Things fluid velocity get handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setVelocityGetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyReadHandler('velocity', async () => {
            return await this.getVelocity(couplingUrl);
        });
    }

    /**
     * Sets Web of Things fluid velocity set handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setVelocitySetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyWriteHandler('velocity', async (velocity) => {
            await this.setVelocity(couplingUrl, velocity);
        });
    }
}

/**
 * Actuator openable properties.
 *
 * This class can be extended by an Actuator class to inherit openable properties.
 * @class HeatingProperties
 */
export class OpenableProperties {
    /**
     * Get open state of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @return {Promise<number>} Temperature of an actuator.
     */
    public async getOpen(couplingUrl: AnyUri): Promise<boolean> {
        let response = await reqGet(`${couplingUrl}/open`);
        return response.data;
    }

    /**
     * Open/close an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @param {boolean} open Flag to open/close an actuator.
     * @return {Promise<any>} Server response.
     */
    public async setOpen(couplingUrl: AnyUri, open: boolean): Promise<any> {
        return await phyngValueSetter(`${couplingUrl}/open`, open);
    }

    /**
     * Sets Web of Things actuator is opened get handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setOpenedGetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyReadHandler('opened', async () => {
            return await this.getOpen(couplingUrl);
        });
    }

    /**
     * Sets Web of Things actuator open handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setOpenSetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setActionHandler('open', async () => {
            await this.setOpen(couplingUrl, true);
        });
    }

    /**
     * Sets Web of Things actuator close handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setCloseSetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setActionHandler('close', async () => {
            await this.setOpen(couplingUrl, false);
        });
    }
}

/**
 * Actuator enableable properties.
 *
 * This class can be extended by an Actuator class to inherit enableable properties.
 * @class EnableableProperties
 */
export class EnableableProperties {
    /**
     * Get enabled state of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @return {Promise<number>} Enabled state of an actuator.
     */
    public async getEnabled(couplingUrl: AnyUri): Promise<boolean> {
        let response = await reqGet(`${couplingUrl}/enabled`);
        return response.data;
    }

    /**
     * Turn on/off an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @param {boolean} enable Flag to turn on/off an actuator.
     * @return {Promise<any>} Server response.
     */
    public async setEnabled(couplingUrl: AnyUri, enable: boolean): Promise<any> {
        return await phyngValueSetter(`${couplingUrl}/enabled`, enable);
    }

    /**
     * Sets Web of Things actuator is enabled get handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setEnabledGetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyReadHandler('enabled', async () => {
            return await this.getEnabled(couplingUrl);
        });
    }

    /**
     * Sets Web of Things actuator turn on handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setTurnOnHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setActionHandler('turnOn', async () => {
            await this.setEnabled(couplingUrl, true);
        });
    }

    /**
     * Sets Web of Things actuator turn off handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setTurnOffHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setActionHandler('turnOff', async () => {
            await this.setEnabled(couplingUrl, false);
        });
    }
}

/**
 * Actuator rotatable properties.
 *
 * This class can be extended by an Actuator class to inherit rotatable properties.
 * @class RotatableProperties
 */
export class RotatableProperties {
    /**
     * Get angle state of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @return {Promise<number>} Angle of an actuator.
     */
    public async getAngle(couplingUrl: AnyUri): Promise<boolean> {
        let response = await reqGet(`${couplingUrl}/angle`);
        return response.data;
    }

    /**
     * Set angle of an actuator.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @param {number} angle actuator angle.
     * @return {Promise<any>} Server response.
     */
    public async setOpen(couplingUrl: AnyUri, angle: number): Promise<any> {
        return await phyngValueSetter(`${couplingUrl}/angle`, angle);
    }

    /**
     * Sets Web of Things actuator angle get handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setAngleGetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyReadHandler('angle', async () => {
            return await this.getAngle(couplingUrl);
        });
    }

    /**
     * Sets Web of Things actuator angle write handler.
     * @param {WoT.ExposedThing} thing WoT exposed thing.
     * @param {AnyUri} couplingUrl URL of a Thing on a simulation server.
     * @protected
     */
    protected setAngleSetHandler(thing: WoT.ExposedThing, couplingUrl: AnyUri): void {
        thing.setPropertyWriteHandler('angle', async (angle) => {
            await this.setOpen(couplingUrl, angle);
        });
    }
}
