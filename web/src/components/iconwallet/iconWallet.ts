import { Mixins, Component } from 'vue-property-decorator'
import {IconMixin} from '@/mixins/IconMixin.ts';
import {mapGetters, mapMutations} from "vuex";

@Component({
    computed: mapGetters({ wallet : 'getWallet'}),
    methods: mapMutations({ setWallet : 'setWallet' })
})
export default class IconWallet extends Mixins(IconMixin)
{
}