import { IWBServer as IWBApp } from "wbserver/iwbserver";

const app = new IWBApp( "./komputor" );
app.loadDiskConfig( );
app.start();
