import {Component, Vue } from "vue-property-decorator";
import IconService from 'icon-sdk-js'


@Component({
    components: {
        IconService
    }
})

export class IconMixin extends Vue {
    public readonly provider = new IconService.HttpProvider('https://bicon.net.solidwallet.io/api/v3');
    public readonly iconService = new IconService(this.provider);
    //public readonly iconBuilder = new this.iconService.IconBuilder();
    public readonly licx_score_address = "cx4322ccf1ad0578a8909a162b9154170859c913eb"


    async getBalances(address ){
        const icxBalance = await this.iconService.getBalance(address).execute();
        const licxBalance = await this.iconService.sendTransaction(this.buildTransaction({
            write: false,
            method: "totalSupply",
            params: {}
        })).execute()
        console.log(licxBalance)
        return BigInt(icxBalance["c"].join(''))
    }

    async getLicxApi(){
        const apiList = await this.iconService.getScoreApi(this.licx_score_address).execute();
        return apiList.getList()
    }

    buildTransaction(_: Record<string, any>){
        let tx;
        /*
        if(_.write){
            tx = new this.iconBuilder.CallTransactionBuilder()
                                .from(_.from)
                                .method(_.method)
                                .value(_.value)

        }
        else{
            new this.iconBuilder.CallBuilder()
                .to(this.licx_score_address)
                .method(_.method)
                .params(_.params)
                .build()
        }
        */
        return tx
    }

    async sendTransaction(){
        //
    }
}