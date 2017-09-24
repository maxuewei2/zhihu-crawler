import json
import sys
def indent(filename):
	with open(filename) as f:
		j=json.loads(f.read())
	strs=filename.split('.')
	with open('indent/'+strs[0]+'_indent_chinese.'+strs[1],'w') as ff:
		ff.write(json.dumps(j,ensure_ascii=False,indent=1).encode('utf-8'))

if __name__=='__main__':
	args=sys.argv
	indent(args[1])
