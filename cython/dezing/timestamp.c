#include "timestamp.h"
#include "sys/time.h"
FILE * logfp;
struct timeval mystime;
double oldtime=0;


int logprint(const char *const message,const int loglevel){
   int retval=0;
   int myerror=0;
   char outmessage[MAX_MESSAGE];
   snprintf(outmessage,MAX_MESSAGE,"C: dezing: %s",message);

  // debug the logging ! 
  // printf("%s\n",outmessage);
  // return(0);
  //
   switch (loglevel){
      case(LEVEL_DEBUG):
         pydebug(outmessage);
      break;
      case(LEVEL_INFO):
         pyinfo(outmessage);
      break;
      case(LEVEL_WARN):
         pywarn(outmessage);
      break;
      case(LEVEL_ERR):
         pyerr(outmessage);
      break;

      default:
      /* fallthru */
      case(LEVEL_USER):
         pyuser(outmessage);
      break;
   }

   //retval=fprintf(logfp,"%s",message);


// #ifdef FLUSH_LOG_FILE
   if( fflush(logfp) == EOF ){
      myerror=errno;
      fprintf(stderr,"ERROR: log file flush failed!\n");
      fprintf(stderr,"%s\n",strerror(myerror));
      return(151);
   };
//#endif
return(retval);
}


void timestamp_open(const char * const logname){
   logfp=fopen(logname,"w");
}

void timestamp_close(void){
   fclose(logfp);
}

void timestamp_init(){
  struct timeval now;
  time_t etimes;
  double nowtime,etime,itime;
  suseconds_t etimeu;
  char message[MAX_MESSAGE];

  gettimeofday(&now,NULL);
  etimes = now.tv_sec - mystime.tv_sec;
  etimeu = now.tv_usec - mystime.tv_usec;
  etime = (double)(etimes)+((double)(etimeu))/(1e6);
  nowtime=(double)(now.tv_sec) + ((double)(now.tv_usec) / 1.0e6);
  oldtime=nowtime;
  itime=nowtime-oldtime;
  snprintf(message,MAX_MESSAGE,"%f %f %f %s",etime,nowtime,itime,"Time stamp reset");
  logprint(message,LEVEL_INFO);
}

void timestamp(const char *const stampmsg,const int loglevel){
  struct timeval now;
  time_t etimes;
  double nowtime,etime,itime;
  suseconds_t etimeu;
  char message[MAX_MESSAGE];

  gettimeofday(&now,NULL);
  etimes = now.tv_sec - mystime.tv_sec;
  etimeu = now.tv_usec - mystime.tv_usec;
  etime = (double)(etimes)+((double)(etimeu))/(1e6);
  nowtime=(double)(now.tv_sec) + ((double)(now.tv_usec) / 1.0e6);
  itime=nowtime-oldtime;
  snprintf(message,MAX_MESSAGE,"%f %f %f %s",etime,nowtime,itime,stampmsg);
  logprint(message,loglevel);
  oldtime=nowtime;
}


int errprint(const char * const message,const int loglevel){
   int retval;
   /* print the message with the program name prefixed, and also echo to the log file */

   if (logfp != NULL){
      retval=fprintf(logfp,"\n*****: %s\n",message);
   }

   retval=fprintf(stderr,"%s\n",message);
   return(retval);
}

int vprint(const char * const message){
   int retval=0;
   if (vflag != 0 ){
      printf("verbose %i: %s\n",vflag,message);
      retval=fprintf(logfp,"%s\n",message);
   }
   return(retval);
}



