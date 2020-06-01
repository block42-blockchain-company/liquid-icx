<template>
    <div class="balance">
        <div class="balance-wrapper">
            <div class="balance-logo">
                <img src="../../assets/ICX-isometric-icon.svg" alt="ICX logo">
            </div>
            <div class="balance-text">
                <div class="balance-title">
                    ICX Balance
                </div>
                <div class="balance-value">
                    <div v-if=wallet>
                        {{ getICX() }}
                    </div>
                    <div v-else>
                        0.0
                    </div>
                </div>
            </div>
        </div>
        <div class="balance-wrapper">
            <div class="balance-logo">
                <img src="../../assets/LICX_isometric-icon.svg" alt="LICX logo">
            </div>
            <div class="balance-text">
                <div class="balance-title">
                    LICX Balance
                </div>
                <div class="balance-value">
                    <div v-if=wallet>
                        {{ getLICX() }}
                    </div>
                    <div v-else>
                        0.0
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<h1 v-if="awesome">Vue is awesome!</h1>
<h1 v-else>Oh no 😢</h1>

<style lang="sccs" src="./balance.scss"></style>
<script lang="ts" src="./balance.ts"></script>
