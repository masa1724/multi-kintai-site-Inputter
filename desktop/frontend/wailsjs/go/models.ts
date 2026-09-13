export namespace main {

	export class InitialData {
	    defaults: Record<string, string>;
	    presets: Record<string, any>;

	    static createFrom(source: any = {}) {
	        return new InitialData(source);
	    }

	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.defaults = source["defaults"];
	        this.presets = source["presets"];
	    }
	}

}
