# decompress_android_backup.py: takes your backup.ab and turns it in to a tar.
# Inf0Junki3, February 2016.
import                  argparse                                                                    
from functools import   partial                                                                     
import                  shutil                                                                      
import                  zlib        
import                  os                                                                

parser = argparse.ArgumentParser("Decompresses an unencrypted android backup file into tar format") 
parser.add_argument("backup_file", help="The file to decompress")                                   
parser.add_argument("dest_tar", help="The destination tar file path")                               

args = parser.parse_args()                                                                          
dest = args.dest_tar                                                                            

print("Stripping off the first 24 bytes of the backup file")                                       
dest_file = open(dest, "wb")                                                                        
orig = open(args.backup_file, "rb")                                                                 
orig.seek(24)                                                                                       
print("Decompressing the file 1024 bytes at a time")
print("Total chunks: "+str(os.path.getsize(args.backup_file)//1024))                      
decompressor = zlib.decompressobj(zlib.MAX_WBITS)
i=0                                                   
for cur_chunk in iter(partial(orig.read, 1024), ""):                                                
    decompressed_chunk = decompressor.decompress(cur_chunk)                                         
    dest_file.write(decompressed_chunk)
    print('Current chunk: %d\r'%i, end="")
    i+=1
dest_file.flush()                                                                                   
dest_file.close()                                                                                   

print("Done! Resulting tar is here: {}".format(dest))