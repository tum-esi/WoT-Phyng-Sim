/**
 * Common Object Interfaces.
 *
 * @file   Contains common interfaces used in the application.
 * @author Anatolii Tsirkunenko
 * @since  29.11.2021
 */

import {AnyUri} from "wot-thing-description-types";

/**
 * Keys to prevent mutation of a
 * fixed length array.
 */
type ArrayLengthMutationKeys = 'splice' | 'push' | 'pop' | 'shift' | 'unshift'

/**
 * Fixed length array type, values are
 * mutable, length is not.
 */
export type FixedLengthArray<T, L extends number, TObj = [T, ...Array<T>]> =
    Pick<TObj, Exclude<keyof TObj, ArrayLengthMutationKeys>>
    & {
    readonly length: L
    [I: number]: T
    [Symbol.iterator]: () => IterableIterator<T>
}

/** Coordinate type x, y, z */
export type Coordinates = FixedLengthArray<number, 3>;

/** Vector type x, y, z */
export type Vector = FixedLengthArray<number, 3>;

/** Size type x, y, z */
export type Size = FixedLengthArray<number, 3>;

/**
 * Phyng properties base interface, used as a
 * base for actuator base and sensor.
 */
interface PhyngPropsBase {
    name: string
    type: string
    /** Phyng location. */
    location?: Coordinates
    /** Phyng in location. */
    locationIn?: Coordinates
    /** Phyng out location. */
    locationOut?: Coordinates
}

/**
 * Actuator base properties, used as a base for
 * actuators created by geometry and template.
 */
export interface ActuatorPropsBase extends PhyngPropsBase {
    /** Custom actuator STL URL TODO: remove this */
    url?: AnyUri
    /** Actuator geometry rotation. */
    rotation?: Vector
    /** Actuator in geometry rotation. */
    rotationIn?: Vector
    /** Actuator out geometry rotation. */
    rotationOut?: Vector
}

/**
 * Created actuator properties, used by
 * actuators created using geometry.
 */
export interface ActuatorPropsCreated extends ActuatorPropsBase {
    /** Actuator geometry dimensions. */
    dimensions: Size
    /** Actuator in geometry dimensions. */
    dimensionsIn?: Size
    /** Actuator out geometry dimensions. */
    dimensionsOut?: Size
}

/**
 * Template actuator properties, used by
 * actuators created using template.
 */
export interface ActuatorPropsStl extends ActuatorPropsBase {
    /** Actuator geometry STL name. */
    stlName: string
    /** Actuator in geometry STL name. */
    stlNameIn?: string
    /** Actuator out geometry STL name. */
    stlNameOut?: string
}

/**
 * Type to combine various actuator
 * properties into a single type.
 */
export type ActuatorProps = ActuatorPropsCreated | ActuatorPropsStl;

/**
 * Sensor properties.
 */
export interface SensorProps extends PhyngPropsBase {
    /** Sensor field to monitor (e.g., "T"). */
    field: string
}

/**
 * Type to combine actuator and sensor
 * properties into a single type.
 */
export type PhyngProps = ActuatorProps | SensorProps;

/**
 * Basic case Web of Phyngs parameters.
 */
export interface CaseParameters {
    /** Case name. */
    name: string
    /** Case type. */
    type: string
    /** Case mesh quality. */
    meshQuality?: number
    /** Case result cleaning limit (0 - no cleaning). */
    cleanLimit?: number
    /** Is case blocking. */
    blocking?: boolean
    /** Is case running in parallel. */
    parallel?: boolean
    /** Amount of cores to run in parallel. */
    cores?: number
    /** Is case running in realtime. */
    realtime?: boolean
    /** Case simulation end time. */
    endTime?: number
}

/**
 * Named Hyperlink REFerences (HREFs).
 */
interface NamedHrefs {
    /** Thing name. */
    name: string
    /** Thing HREFs. */
    hrefs: AnyUri[]
}

/**
 * Case Hyperlink REFerences (HREFs).
 */
export interface CaseHrefs extends NamedHrefs {
}

/**
 * Phyng Hyperlink REFerences (HREFs).
 */
export interface PhyngHrefs extends NamedHrefs {
    /** Phyng type */
    type: string
}

/**
 * Simulation errors object to read.
 */
export interface SimulationErrors {
    /** Error shortened texts array. */
    texts: string[]
    /** Full error traces array. */
    traces: string[]
}

export interface CaseDescription extends WoT.ThingDescription {
    '@type'?: string;
    links: {rel: string, href: string, contentType: string}[]
    sysProperties: CaseParameters;
}

export interface PhysicalDescription extends WoT.ThingDescription {
    '@type'?: string;
    links: {rel: string, href: string, contentType: string}[]
    phyProperties: PhyngProps;
}
