import {Component, Vue } from "vue-property-decorator";
import IconService from 'icon-sdk-js'
import store from '../store/index'

@Component({
    components: {
        IconService
    }
})

export class IconMixin extends Vue {
    public readonly provider = new IconService.HttpProvider('https://bicon.net.solidwallet.io/api/v3');
    public readonly iconService = new IconService(this.provider);


}