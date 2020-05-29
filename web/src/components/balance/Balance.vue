<template>
    <div class="balance">
        <div class="balance-wrapper">
                <div class="balance-logo">
                    <img src="../../assets/ICX-isometric-icon.svg">
                </div>
                <div class="balance-text">
                    <div class="balance-title">
                        ICX Balance
                    </div>
                    <div class="balance-value">
                        {{ wallet.balances.icx }}
                    </div>
                </div>
        </div>
        <div class="balance-wrapper">
                <div class="balance-logo">
                    <img src="../../assets/LICX_isometric-icon.svg">
                </div>
                <div class="balance-text">
                    <div class="balance-title">
                        LICX Balance
                    </div>
                    <div class="balance-value">
                        {{ wallet.balances.licx }}
                    </div>
                </div>
            </div>
    </div>
</template>

<style lang="sccs" src="./balance.scss"></style>
<script lang="ts" src="./balance.ts"></script>
