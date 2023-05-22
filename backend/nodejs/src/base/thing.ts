/**
 * Thing module.
 *
 * @file   Contains an AbstractThing class that is used by all node-things in this application.
 * @author Anatolii Tsirkunenko
 * @since  28.11.2021
 */
import {AnyUri, FormElementRoot} from 'wot-thing-description-types';

const path = require('path');
const glob = require('glob')

const TMS_PATH = path.resolve(`${__dirname}/../../tms`);
const GLOB_PATTERN = `${TMS_PATH}/**/*.model.json`
const TM_PATHS: { [file: string]: string } = {};

let _tmPathsArr = glob.sync(GLOB_PATTERN, {});
let _re = /.+\/(.+\.model\.json)/;
_tmPathsArr.forEach((path: string) => {
    let tmFile = path.match(_re);
    if (!tmFile) return;
    TM_PATHS[tmFile[1]] = path;
});

/**
 * An abstract thing.
 *
 * Abstract class used by all node-wot
 * things in this application.
 * @class AbstractThing
 * @abstract
 */
export abstract class AbstractThing {
    /** Web of Things interface. */
    protected wot: WoT.WoT;
    /** Web of Things exposed thing. */
    protected thing!: WoT.ExposedThing;
    /** IP address of a simulation server. */
    protected host: AnyUri;
    /** URL of a Thing on a simulation server. */
    public couplingUrl: AnyUri;
    /** Promise that resolves once a Thing is initialized. */
    public ready: Promise<boolean>;

    /**
     * Adds property handlers to an exposed thing.
     * @protected
     */
    protected abstract addPropertyHandlers(): void;

    /**
     * Adds action handlers to an exposed thing.
     * @protected
     */
    protected abstract addActionHandlers(): void;

    /**
     * Adds event handlers to an exposed thing.
     * @protected
     */
    protected abstract addEventHandlers(): void;

    protected constructor(host: string, wot: WoT.WoT, tm: WoT.ThingDescription) {
        this.wot = wot;
        this.host = host;
        this.couplingUrl = host;
        this.ready = new Promise<boolean>(async (resolve) => {
            try {
                await this.createFromTm(tm);
                resolve(true);
            } catch (e) {
                // TODO: additional error handling
                console.error(e);
            }
        })
    }

    /**
     * Extends given thing model via linked thing models (inheritance).
     * @param {WoT.ThingDescription} tm Thing model to extend.
     * @return {WoT.ThingDescription} Extended thing model.
     * @protected
     */
    public static extendTmByLink(tm: WoT.ThingDescription): WoT.ThingDescription {
        let extendedTm = {...tm};
        if ('links' in extendedTm) {
            for (const link of extendedTm.links) {
                if (link.rel === 'tm:extends') {
                    let filePath: string;
                    if (link.href.includes('file://')) {
                        filePath = link.href.replace('file://', '');
                    } else {
                        filePath = TM_PATHS[link.href];
                    }
                    let parentTm = {...require(filePath)};
                    if ('links' in parentTm) {
                        parentTm = this.extendTmByLink(parentTm);
                    }
                    let properties = 'properties';
                    let actions = 'actions';
                    let events = 'events';
                    let securityDefinitions = 'securityDefinitions';
                    if (properties in parentTm) {
                        if (properties in extendedTm) {
                            extendedTm.properties = {...parentTm.properties, ...extendedTm.properties};
                        } else {
                            extendedTm.properties = {...parentTm.properties};
                        }
                    }
                    if (actions in parentTm) {
                        if (actions in extendedTm) {
                            extendedTm.actions = {...parentTm.actions, ...extendedTm.actions};
                        } else {
                            extendedTm.actions = {...parentTm.actions};
                        }
                    }
                    if (events in parentTm) {
                        if (events in extendedTm) {
                            extendedTm.events = {...parentTm.events, ...extendedTm.events};
                        } else {
                            extendedTm.events = {...parentTm.events};
                        }
                    }
                    if (!(securityDefinitions in extendedTm)) {
                        extendedTm.securityDefinitions = {...parentTm.securityDefinitions};
                    }
                }
            }
            delete extendedTm.links
        }
        return extendedTm;
    }

    /**
     * Creates, exposes and attaches handler to an
     * exposed thing using a give thing model.
     * @param tm Thing model.
     * @protected
     * @async
     */
    protected async createFromTm(tm: WoT.ThingDescription): Promise<void> {
        let extendedTm = AbstractThing.extendTmByLink(tm);
        this.thing = await this.wot.produce(extendedTm)
        await this.thing.expose();
        this.addPropertyHandlers();
        this.addActionHandlers();
        this.addEventHandlers();
    }

    /**
     * Gets Hypertext REFerences of current thing.
     * @return {AnyUri[]} HREFs.
     */
    public getHrefs(): AnyUri[] {
        let forms: [FormElementRoot, ...FormElementRoot[]] = this.thing.getThingDescription().forms;
        forms.forEach(form => form.href = form.href.split('/all')[0]);
        return forms.map(({href}) => href);
    }

    /**
     * Destroys this exposed thing.
     * @async
     */
    public async destroy(): Promise<void> {
        await this.thing.destroy();
        // TODO: delete something else?
    }
}
