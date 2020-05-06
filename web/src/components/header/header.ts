import { Mixins, Component } from 'vue-property-decorator'
import {IconMixin} from '@/mixins/IconMixin.ts';
import store from '@/store/index'
import {mapState, mapMutations, mapGetters} from "vuex";


@Component({
    computed: mapGetters({ wallet : 'getWallet'}),
    methods: mapMutations({ setWallet : 'setWallet' })
})
export default class Header extends Mixins(IconMixin)
{

}